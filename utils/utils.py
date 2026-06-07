from multiprocessing import Process, Queue
from re import fullmatch
from typing import Any, Callable, Optional
from SPARQLWrapper import JSON, SPARQLWrapper
from numpy import array, dot, mean, zeros
from numpy.linalg import norm
from utils.constants import AGENT, BASE_URLS, SBERT_MODEL, WIKI2VEC_MODEL, WIKIDATA_URL
from sklearn.metrics.pairwise import cosine_similarity
from utils.enums import EmbeddingType, ResourceType
from utils.logger import LOGGER
from sentence_transformers.util import cos_sim
from sentence_transformers import SentenceTransformer
from wikipedia2vec import Wikipedia2Vec
from queue import Empty as QueueEmptyException

def load_model(embedding_type: EmbeddingType = EmbeddingType.WIKI2VEC):
    if embedding_type == EmbeddingType.WIKI2VEC:
        return Wikipedia2Vec.load(WIKI2VEC_MODEL)
    
    if embedding_type == EmbeddingType.SBERT:
        return SentenceTransformer(SBERT_MODEL)
    
    if embedding_type == EmbeddingType.WORD2VEC:
        from word2vec import load_data
    else:
        from fasttext import load_data
    
    return load_data()

def claude_message(epel, lista, target_node):
    return f"do not insert δικους σου nodes αλλα επελεξε ακριβως {epel} αν ειναι διαθεσιμoi απο την {lista} αυτους που πλησιαζουν πιο πολυ  α΄΄΄΄λλα και αλλους που θα μπορουσαν πιο πιθανα να οδηγησουν στον κομβο {target_node} επελεξε συνολικα +{epel} και δωσε τους ενα σκορ εγγυτητας με τρια δεκαδικα. εαν δεν πλησιαζει πολυ δωσε σκορ κατω απο 0.4. Αν πλησιζει πολυ δωσε πανω απο 0.7. Επελεξε τους κομβους με τα μεγαλυτερα σκορ. Επισης μην επιλεξεις nodes που αναφερονται σε γενικες κατηγοριες αλλα μονο σε υπαρκτα entities. Return them  as string of entities. An entity is node comma score. Score is from 0.0 for irrelevant to target to 1 .if the node includes the word of the target, return as a score 1.0 .Do not comment scores.If target node is exacly found in list give it score 500.0. Final string is entity#entity#entity etc mean seperate entities with without headers # Return plain string.Αν δεν ειναι διαθεσιμοι 6 κομβοι δεν πειραζει και ΜΗΝ ΔΗΜΙΟΥΡΓΗΣΕΙΣ ΚΟΜΒΟΥΣ ΑΠΟ ΤΗΝ ΔΙΚΗ ΣΟΥ ΓΝΩΣΗ που δεν υπαρχουν στην λιστα. ΑΚΟΜΑ ΚΑΙ ΕΝΑΣ ΝΑ ΕΙΝΑΙ Ο ΚΟΜΒΟΣ ΕΠΕΣΤΡΕΨΕ ΤΟΝ"

def worker(embedding_type: EmbeddingType, task_queue: Queue, result_queue: Queue):
    model = load_model(embedding_type)
    while True:
        task = task_queue.get()
        if task is None:  # Poison pill to shutdown
            break
        func, args = task
        try:
            result = func(model, *args)
            result_queue.put(result)
        except Exception as e:
            result_queue.put(e)

def timeout(func: Callable[[Any, str, str, Optional[EmbeddingType]], tuple], args: tuple, embedding_type: EmbeddingType=EmbeddingType.WIKI2VEC, timeout: int=360):
    task_queue = Queue()
    result_queue = Queue()
    p = Process(target=worker, args=(embedding_type, task_queue, result_queue))
    p.start()

    task_queue.put((func, args))

    try:
        result = result_queue.get(timeout=timeout)
    except QueueEmptyException:
        p.terminate()
        p.join()
        return timeout,0,0,0,[] 

    task_queue.put(None)  # Tell worker to stop
    p.join()
    
    if isinstance(result, Exception):
        raise result  # If you want to propagate errors

    return result

def _wrapper(func: Callable[[Any, str, str, Optional[EmbeddingType]], tuple], entity1: str, entity2: str, embedding_type: EmbeddingType, queue: Queue):
    model = load_model(embedding_type)
    result = func(model, entity1, entity2, embedding_type) if embedding_type is not None else func(model, entity1, entity2)
    queue.put(result)

def timeout2(func: Callable[[Any, str, str, Optional[EmbeddingType]], tuple], entity1: str, entity2: str, embedding_type: EmbeddingType=None, timeout: int=360):
    queue = Queue()
    process = Process(target=_wrapper, args=(func, entity1, entity2, embedding_type, queue))
    process.start()
    process.join(timeout)

    if process.is_alive():
        LOGGER.error(f"Pair {(entity1, entity2)} timed out. Continuing...")
        process.terminate()
        process.join()
    
    return queue.get() if not queue.empty() else timeout,0,0,0,[]

def read_conf(filename: str):
    with open(filename) as pairs:
        result = list()
        for pair in pairs.readlines():
            if pair.startswith("#"):
                LOGGER.info(f"Skipping {pair}...")
                continue
            pair_sp = pair.split(",")
            result.append((pair_sp[0].strip(), pair_sp[1].strip()))
        return result

def execute_query(sparql: SPARQLWrapper, query: str):
    """
    Εκτελεί το SPARQL query και επιστρέφει τα αποτελέσματα.
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(60)
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        LOGGER.error(f"Error executing query: {e}")
        return None

def construct_query(entity1: str, entity2: str, depth: int, wikidata: bool):
    """
    Δημιουργεί ένα SPARQL query για την εύρεση μονοπατιού μεταξύ δύο οντοτήτων.
    Εξαιρεί τριπλέτες με predicate `http://dbpedia.org/ontology/wikiPageWikiLink`.
    """
    
    if not wikidata and depth==1:
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT * WHERE {{
        <{entity1}> ?p0 <{entity2}> .
        FILTER (?p0 != <http://dbpedia.org/ontology/wikiPageWikiLink>)
        """
    else:
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT * WHERE {{
        <{entity1}> ?p0 ?x1 .
        FILTER (?p0 != <http://dbpedia.org/ontology/wikiPageWikiLink>)
        """
        if not wikidata:
            depth -= 1
        for i in range(1, depth):
            query += f"?x{i} ?p{i} ?x{i+1} .\n"
            query += f"FILTER (?p{i} != <http://dbpedia.org/ontology/wikiPageWikiLink>)\n"

       
        query += f"?x{depth} ?p{depth} <{entity2}> .\n"
        query += f"FILTER (?p{depth} != <http://dbpedia.org/ontology/wikiPageWikiLink>)\n"

    query += "} limit 1"
    return query

def get_entity_label(entity_id: str, agent: bool=False, resource_type: ResourceType=ResourceType.DBPEDIA):
    sparql = SPARQLWrapper(BASE_URLS[resource_type], agent=AGENT) if agent else SPARQLWrapper(BASE_URLS[resource_type])

    
    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      BIND(<{entity_id}> AS ?item)
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    # Extract label from the results
    if results["results"]["bindings"]:
        label = results["results"]["bindings"][0]["itemLabel"]["value"]
        return label
    
    return None

def get_entity_similarity(entity1: str, entity2: str, model, embedding_type: EmbeddingType=EmbeddingType.WIKI2VEC):
    """
    Calculate similarity between two Wikipedia entities.
    
    Args:
        entity1 (str): First entity title
        entity2 (str): Second entity title
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if embedding_type == EmbeddingType.SBERT:
        return float(get_sbert_similarity(entity1, entity2, model))
    
    if embedding_type in [EmbeddingType.FASTTEXT, EmbeddingType.WORD2VEC]:
        return get_pretrained_similarity(entity1, entity2, model)
    
    try:
        if not entity1.strip() or not entity2.strip():
            return 0
        # Get entity embeddings
        entity1_vec = model.get_entity_vector(entity1.strip())
        entity2_vec = model.get_entity_vector(entity2.strip())
        
        # Calculate cosine similarity
        similarity: float = dot(entity1_vec, entity2_vec) / (
        norm(entity1_vec) * norm(entity2_vec)
        )
        return similarity
    except KeyError as e:
        LOGGER.error(f"Entity not found: {e.__str__()}")
        return 0

def is_english_only(s):
    return bool(fullmatch(r"[A-Za-z0-9 /\-()_:/.]+", s))

def get_wikidata_uri(label: str):
    sparql = SPARQLWrapper(WIKIDATA_URL,agent=AGENT)
    
    query = f"""
    SELECT ?item WHERE {{
      ?item rdfs:label "{label}"@en.
    }}
    LIMIT 1
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]["item"]["value"]
    return None

def get_embedding(name: str, model):
    words = name.lower().split()
    vectors = [model[word] for word in words if word in model]
    return mean(vectors, axis=0) if vectors else zeros(300)

def get_pretrained_similarity(entity1: str, entity2: str, model):
    embeddings = array([get_embedding(entity1, model), get_embedding(entity2, model)])
    similarity = cosine_similarity(embeddings)
    return similarity[0, 1]

def get_sbert_similarity(entity1: str, entity2: str, model: SentenceTransformer):
    embeddings = model.encode([entity1, entity2], convert_to_tensor=True)
    similarity = cos_sim(embeddings, embeddings)
    return similarity[0, 1]