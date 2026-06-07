from time import time

from utils.constants import DBPEDIA_RESOURCE_URL, DBPEDIA_URL
from utils.enums import EmbeddingType
from utils.logger import LOGGER
from utils.pathfinder import find_path, find_path_between_nodes
from utils.utils import get_entity_similarity

def white_rabbit(model, entity1: str, entity2: str, acceptance_threshold: float=1.0):
    """_summary_

    Args:
        model (_type_): _description_
        entity1 (str): _description_
        entity2 (str): _description_
        acceptance_threshold (float, optional): _description_. Defaults to 1.0.

    Returns:
        _type_: _description_
    """
    start_node=f"{DBPEDIA_RESOURCE_URL}/{entity1}"
    target_node=f"{DBPEDIA_RESOURCE_URL}/{entity2}"
    now = time()
    word_entity_sim = get_entity_similarity(entity1, entity2, model)
    
    LOGGER.info(f"Similarity between {start_node} and {target_node}: {word_entity_sim}")
    if word_entity_sim >= acceptance_threshold:
        return round(time()-now), 1, round(word_entity_sim, 2), round(word_entity_sim, 2), [(start_node, "", target_node)]
    
    counter = 1
    depth,path = find_path_between_nodes(start_node, target_node, f"{DBPEDIA_URL}/query", model)
    if not path:
        return round(time()-now), 0, 0, 0, []
    
    totalp=0.0
    totale=0.0
    now2 = time()
    
    lana=len(path)
    ida=1
    for triple in path:
        xa0= triple[0][0].rsplit('/', 1)[-1]
        xa2= triple[2][0].rsplit('/', 1)[-1]
        xa0=xa0.replace("_"," ").replace("-",' ')
        xa2=xa2.replace("_"," ").replace("-",' ')
        xa3=entity2
        xa3=xa3.replace("_"," ").replace("-",' ')
    
        word_entity_similarity = get_entity_similarity(xa0, xa2, model)
        totalp+= word_entity_similarity
    
        word_entity_similarity2 = get_entity_similarity(xa0, xa3, model)
        totale+= word_entity_similarity2
        LOGGER.info(f"Similarity between {xa0} and {xa2}: {word_entity_similarity} {word_entity_similarity2} ")
        ida=ida+1
        if ida==lana:
            break
        
        counter+=1
        if word_entity_similarity >= acceptance_threshold:
            nn = totalp/(float(counter))
            nt = totale/(float(counter))
            return round(now2-now), counter, round(nn, 2), round(nt, 2), path
        
    nn = totalp/(float(depth))
    nt = totale/(float(depth))
    return round(now2-now), depth, round(nn, 2), round(nt, 2), path

def query_expansion(model, entity1: str, entity2: str, acceptance_threshold: float=1.0):
    """_summary_

    Args:
        model (_type_): _description_
        entity1 (str): _description_
        entity2 (str): _description_
        acceptance_threshold (float, optional): _description_. Defaults to 1.0.

    Returns:
        _type_: _description_
    """
    now = time()
    paths: list[tuple[str, str, str]] = []
    depth, results = find_path(entity1, entity2)

    if not results:
        return round(time()-now), 0, 0, 0, []
    
    triples: list[tuple[str, str, str]] = []
    data=results
    first_p_key = next(key for key in data[0].keys() if key.startswith('p'))

    # Find the last 'p' key (e.g., p5, p10, etc.)
    last_p_key = next(key for key in reversed(data[0].keys()) if key.startswith('p'))

    try:
        # Find the first 'x' key (e.g., x1)
        first_x_key = next(key for key in data[0].keys() if key.startswith('x'))

        # Find the last 'x' key (e.g., x5, x7, etc.)
        last_x_key = next(key for key in reversed(data[0].keys()) if key.startswith('x'))
        
        first_x_value = data[0][first_x_key]['value']
        last_x_value = data[0][last_x_key]['value']
    except StopIteration:
        first_x_value = entity1
        last_x_value = entity2
    # Extract the corresponding values for first and last 'p' and 'x' keys
    first_p_value = data[0][first_p_key]['value']
    last_p_value = data[0][last_p_key]['value']

    for entry in data:
        # Iterate over the 'x' and 'p' pairs and form the desired triples
        for i in range(1, len(entry)//2):  # Skip p0
            x_key = f"x{i}"
            p_key = f"p{i}"
    
            # Get the values
            subject = entry[x_key]['value']
            predicate = entry[p_key]['value']
            object_ = entry[f"x{i+1}"]['value'] if f"x{i+1}" in entry else None
            
            if object_:
                triples.append((subject, predicate, object_))
    
    totalp=0.0
    totale=0.0
    now2 = time()

    paths.append((entity1, first_p_value, first_x_value))
    xa2= first_x_value.rsplit('/', 1)[-1].replace("_"," ").replace("-"," ")
    entity1=entity1.replace("_"," ").replace("-"," ")
    entity2= entity2.replace("_"," ").replace("-"," ")

    word_entity_similarity = get_entity_similarity(entity1, xa2, model)
    totalp+= word_entity_similarity
    word_entity_similarity2 = get_entity_similarity(entity1, entity2, model)
    totale+= word_entity_similarity2

    LOGGER.info(f"Similarity between {entity1} and {xa2}: {word_entity_similarity}")
    if word_entity_similarity >= acceptance_threshold:
        return round(now2-now), depth, round(totalp, 2), round(totale, 2), paths
    
    counter = 1
    for triple in triples:
        xa0= triple[0].rsplit('/', 1)[-1].replace("_"," ").replace("-"," ")
        xa2= triple[2].rsplit('/', 1)[-1].replace("_"," ").replace("-"," ")

        word_entity_similarity = get_entity_similarity(xa0, xa2, model)
        totalp+= word_entity_similarity

        word_entity_similarity2 = get_entity_similarity(xa0, entity2, model)
        totale+= word_entity_similarity2
        LOGGER.info(f"Similarity between {xa0} and {xa2}: {word_entity_similarity}")
        
        counter += 1
        paths.append(triple)

        if word_entity_similarity >= acceptance_threshold:
            nn = totalp/(float(counter))
            nt = totale/(float(counter))
            return round(now2-now), counter, round(nn, 2), round(nt, 2), paths


    paths.append((last_x_value, last_p_value, entity2))
    xa0= last_x_value.rsplit('/', 1)[-1].replace("_"," ").replace("-"," ")
    word_entity_similarity = get_entity_similarity(xa0, entity2, model)

    totalp+= word_entity_similarity

    word_entity_similarity2 = get_entity_similarity(xa0, entity2, model)
    totale+= word_entity_similarity2
    LOGGER.info(f"Similarity between {xa0} and {entity2}: {word_entity_similarity}")
    nn = totalp/(float(depth))
    nt = totale/(float(depth))
    return round(now2-now), depth, round(nn, 2), round(nt, 2), paths

def embedding(model, entity1: str, entity2: str, embedding_type: EmbeddingType, acceptance_threshold: float=1.0):
    """_summary_

    Args:
        model (_type_): _description_
        entity1 (str): _description_
        entity2 (str): _description_
        embedding_type (EmbeddingType): _description_
        acceptance_threshold (float, optional): _description_. Defaults to 1.0.

    Returns:
        _type_: _description_
    """
    start_node=f"{DBPEDIA_RESOURCE_URL}/{entity1}"
    target_node=f"{DBPEDIA_RESOURCE_URL}/{entity2}"
    now = time()
    word_entity_sim = get_entity_similarity(entity1, entity2, model, embedding_type)
    
    LOGGER.info(f"Similarity between {start_node} and {target_node}: {word_entity_sim}")
    if word_entity_sim >= acceptance_threshold:
        return round(time()-now), 1, round(word_entity_sim, 2), round(word_entity_sim, 2), [(start_node, "", target_node)]
    
    counter = 1
    depth,path = find_path_between_nodes(start_node, target_node, f"{DBPEDIA_URL}/query", model, embedding_type=embedding_type)
    if not path:
        return round(time()-now), 0, 0, 0, []
    
    totalp=0.0
    totale=0.0
    now2 = time()
    
    lana=len(path)
    ida=1
    for triple in path:
        xa0= triple[0][0].rsplit('/', 1)[-1]
        xa2= triple[2][0].rsplit('/', 1)[-1]
        xa0=xa0.replace("_"," ").replace("-",' ')
        xa2=xa2.replace("_"," ").replace("-",' ')
        xa3=entity2
        xa3=xa3.replace("_"," ").replace("-",' ')
    
        word_entity_similarity = get_entity_similarity(xa0, xa2, model, embedding_type)
        totalp+= word_entity_similarity
    
        word_entity_similarity2 = get_entity_similarity(xa0, xa3, model, embedding_type)
        totale+= word_entity_similarity2
        LOGGER.info(f"Similarity between {xa0} and {xa2}: {word_entity_similarity} {word_entity_similarity2} ")
        ida=ida+1
        if ida==lana:
            break
        
        counter+=1
        if word_entity_similarity >= acceptance_threshold:
            nn = totalp/(float(counter))
            nt = totale/(float(counter))
            return round(now2-now), counter, round(nn, 2), round(nt, 2), path
        
    nn = totalp/(float(depth))
    nt = totale/(float(depth))
    return round(now2-now), depth, round(nn, 2), round(nt, 2), path

def llm(model, entity1: str, entity2: str, acceptance_threshold: float=1.0):
    """_summary_

    Args:
        model (_type_): _description_
        entity1 (str): _description_
        entity2 (str): _description_
        acceptance_threshold (float, optional): _description_. Defaults to 1.0.

    Returns:
        _type_: _description_
    """
    start_node=f"{DBPEDIA_RESOURCE_URL}/{entity1}"
    target_node=f"{DBPEDIA_RESOURCE_URL}/{entity2}"
    now = time()
    word_entity_sim = get_entity_similarity(entity1, entity2, model)
    
    LOGGER.info(f"Similarity between {start_node} and {target_node}: {word_entity_sim}")
    if word_entity_sim >= acceptance_threshold:
        return round(time()-now), 1, round(word_entity_sim, 2), round(word_entity_sim, 2), [(start_node, "", target_node)]
    
    counter = 1
    depth,path = find_path_between_nodes(start_node, target_node, f"{DBPEDIA_URL}/query", llm=True)
    if not path:
        return round(time()-now), 0, 0, 0, []
    
    totalp=0.0
    totale=0.0
    now2 = time()
    
    lana=len(path)
    ida=1
    for triple in path:
        xa0= triple[0][0].rsplit('/', 1)[-1]
        xa2= triple[2][0].rsplit('/', 1)[-1]
        xa0=xa0.replace("_"," ").replace("-",' ')
        xa2=xa2.replace("_"," ").replace("-",' ')
        xa3=entity2
        xa3=xa3.replace("_"," ").replace("-",' ')
    
        word_entity_similarity = get_entity_similarity(xa0, xa2, model)
        totalp+= word_entity_similarity
    
        word_entity_similarity2 = get_entity_similarity(xa0, xa3, model)
        totale+= word_entity_similarity2
        LOGGER.info(f"Similarity between {xa0} and {xa2}: {word_entity_similarity} {word_entity_similarity2} ")
        ida=ida+1
        if ida==lana:
            break
        
        counter+=1
        if word_entity_similarity >= acceptance_threshold:
            nn = totalp/(float(counter))
            nt = totale/(float(counter))
            return round(now2-now), counter, round(nn, 2), round(nt, 2), path
    
    nn = totalp/(float(depth))
    nt = totale/(float(depth))
    return round(now2-now), depth, round(nn, 2), round(nt, 2), path