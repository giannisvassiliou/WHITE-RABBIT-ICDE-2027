from json import loads
from traceback import print_exc
from SPARQLWrapper import JSON, SPARQLWrapper
from anthropic import Anthropic

from utils.constants import AGENT, BASE_URLS, CLAUDE_MODEL, RESOURCE_URLS, SPARQL_PREFIX, WIKIDATA_URL
from utils.enums import EmbeddingType, ResourceType
from utils.logger import LOGGER
from utils.utils import claude_message, construct_query, execute_query, get_entity_similarity, is_english_only

def find_path(entity1: str, entity2: str, max_depth: int=15, agent: bool=False, resource_type: ResourceType=ResourceType.DBPEDIA):
    """
    Βρίσκει μονοπάτι μεταξύ δύο οντοτήτων στο DBpedia μέσω SPARQL queries.
    """
    sparql = SPARQLWrapper(BASE_URLS[resource_type], agent=AGENT) if agent else SPARQLWrapper(BASE_URLS[resource_type])
    # Μετατροπή οντοτήτων σε πλήρη URIs εάν δεν έχουν ήδη.
    if not entity1.startswith("http"):
        entity1 = f"{RESOURCE_URLS[resource_type]}/{entity1}"
    if not entity2.startswith("http"):
        entity2 = f"{RESOURCE_URLS[resource_type]}/{entity2}"

    # Επαναληπτική εκτέλεση queries μέχρι το μέγιστο βάθος
    for depth in range(1, max_depth + 1):
        LOGGER.info(f"Executing query with depth {depth}...")
        query = construct_query(entity1, entity2, depth,(resource_type == ResourceType.WIKIDATA))

        results = execute_query(sparql, query)

        if results and results["results"]["bindings"]:
            LOGGER.info(f"Path found at depth {depth}!")
            return depth, results["results"]["bindings"]

    LOGGER.error("No path found within the given depth.")
    return None, None

def find_path_between_nodes(start_node: str, target_node: str, endpoint: str, model, llm: bool=False, agent: bool=False, resource_type: ResourceType=ResourceType.DBPEDIA, embedding_type: EmbeddingType=EmbeddingType.WIKI2VEC):
    sparql = SPARQLWrapper(endpoint, agent=AGENT) if agent else SPARQLWrapper(endpoint)
    visited = set()
    # Track visited nodes
    sstart=0
    queue = [([start_node,0.0], []),([start_node,0.0], [])]  # Queue of (current_node, path_so_far)

    if llm:
        client = Anthropic()
        count = client.beta.messages.count_tokens(
            model=CLAUDE_MODEL,
            messages=[
                {"role": "user", "content": "Hello, world"}
            ]
        )
        LOGGER.info(F"Tokens remaining: {count.input_tokens}") 

    while queue:
        lis=[]
        it=0
        for a in queue:
            c,_=a
            it=it+1
            lis.append(c[0]+" "+str(c[1]))
        current_node, path = queue.pop(0)
        
        result2 = current_node[0].split("resource/")[-1]
     

        if current_node[0] in visited:
            continue
        visited.add(current_node[0])

        # Check if we reached the target node
        if current_node[0] == target_node or (not llm and result2 in target_node):
            path=path + [(current_node, "reached", target_node)]
            return len(path)-1, path

        # Query outgoing links from the current node
        
        stoa=f""" {SPARQL_PREFIX} 
        SELECT  {'distinct' if not llm else ""} ?next_node ?predicate WHERE {{
             <{current_node[0]}> ?predicate ?next_node .
               ?next_node rdfs:label ?label .
                               FILTER (?predicate != <http://dbpedia.org/ontology/wikiPageWikiLink>)

                FILTER (lang(?label) = "en").
                
            }}
            """
        sparql.setQuery(stoa)
        
        sparql.setReturnFormat(JSON)

        try:
            results = sparql.query().convert()
            if isinstance(results, bytes):  # Decode if necessary
                results = loads(results.decode("utf-8"))
        except Exception as e:
            LOGGER.error(f"Error querying SPARQL endpoint: {e}")
            print_exc() 
            continue
        lista=[]
        lista2=[]
        dicta={}
        # Process each outgoing link and add it to the queue if not visited
        if results.get("results") and results["results"].get("bindings"):
            for result in results["results"]["bindings"]:
                next_node = result["next_node"]["value"]
                predicate = result["predicate"]["value"]
                dicta[next_node]=predicate
                
                # Append to the path and add to the queue
                if is_english_only(next_node) and next_node not in visited and "resource" in next_node and 'Category' not in next_node and 'Template' not in next_node:
                    lista.append(next_node)
                    lista2.append(predicate+" "+next_node)
                    
        if lista.__len__()>1:
            epel=3
            toyl=lista.__len__()
            if toyl>6 and toyl<=12:
                epel=11
            elif toyl>12:
                epel=toyl-1 if not llm else 11
            else:
                epel=toyl-1

            if llm:
                stringas=claude_message(epel, lista, target_node)
                message = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1000,
                    temperature=0,
                    system="You are a DBPEDIA SPECIALIST",
                    messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": stringas
                                    }
                                ]
                            }
                        ]
                )
                response=message.content[0].text
            else:
                si=target_node
                si1=si.rsplit('/', 1)[-1]
                si1=si1.replace("_"," ")
                oka=""
                prf = f"{RESOURCE_URLS[resource_type]}/"    
                          
                loa=[]
                for l in lista:
                    last_part = l.rsplit('/', 1)[-1]
                    last_part2=last_part.replace("_"," ")
                    word_entity_sim = get_entity_similarity(si1, last_part2, model, embedding_type=embedding_type)

                    LOGGER.info(f"Similarity between {si1} and {last_part2}: {word_entity_sim}")
                    if word_entity_sim is not None:
                        oka=oka+prf+last_part+","+str(word_entity_sim)+"#"
                        lss=[prf+last_part,float(word_entity_sim)]
                        loa.append(lss)
                        
                oka=''
                apa=0
                # Sort in descending order based on the second element (similarity score)
                sorted_data = sorted(loa, key=lambda x: x[1], reverse=True)
                
                # Print sorted list
                for item in sorted_data:
                    a1=item[0]
                    a2=item[1]
                    oka=oka+a1+","+str(a2)+"#"
                    if apa==epel:
                        break
                    apa=apa+1

                oka=oka.rstrip()
                response=oka
            ra=response
            ra=ra.replace('\n','')
    
            
            tups=ra.split('#')
            
            if lista:
                for ft in tups:
                    try:
                        sco=ft.split(',')
                        if len(sco) <= 1:
                            continue
                        sco[0]=sco[0].replace(' ','')
                        sco[0]=sco[0].replace('\'','')
                        sco[1]=sco[1].replace('\'','')
                        position=-1
                        if sstart==0:
                            
                            position=0
                            sstart=1
                            queue.insert(position,(sco, path + [(current_node, dicta[sco[0]], sco)]))
                        else:          
                            i=0  
                            
                            while True:
                                if i>=queue.__len__():
                                    break
                                a,_=queue[i]
                                try:
                                    if float(a[1])<float(sco[1]):
                                            position=i
                                            break
                                    
                                    
                                except Exception as e:
                                    LOGGER.error(f"An error occurred: {e}")
                                    print_exc() 
                                    break
                                    
                                i=i+1 
                            if i>=len(queue):
                                position=len(queue)-1
                                
                            if position != -1:
                                queue.insert(position,(sco, path + [(current_node, dicta[sco[0]], sco)]))
                    except Exception as e:
                        LOGGER.error(f"An error occurred: {e}")
                        print_exc() 
                        
    # If queue exhausts without finding target
    return 0, []

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

def find_path_between_nodes_emb_wiki(start_node_raw: str, target_node_raw: str, model, llm: bool=False, embedding_type: EmbeddingType=EmbeddingType.WIKI2VEC):
    sparql = SPARQLWrapper(WIKIDATA_URL,agent=AGENT)
    visited = set()
    dicta11={}
    dicta22={}
    dicta33={}
    dicta22[start_node_raw]=start_node_raw
    start_node=get_wikidata_uri(start_node_raw)
    target_node=get_wikidata_uri(target_node_raw)
    sstart=0
    queue = [([start_node,0.0], []),([start_node,0.0], [])]  # Queue of (current_node, path_so_far)

    if llm:
        client = Anthropic()
        count = client.beta.messages.count_tokens(
            model=CLAUDE_MODEL,
            messages=[
                {"role": "user", "content": "Hello, world"}
            ]
        )
        LOGGER.info(F"Tokens remaining: {count.input_tokens}") 
    
    while queue:
        lis=[]
        it=0
        for a in queue:
            c,_=a
            it=it+1
            lis.append(c[0]+" "+str(c[1]))
        current_node, path = queue.pop(0)
        
        result2 = current_node[0].split("resource/")[-1]
     
        if current_node[0] in visited:
            continue
        visited.add(current_node[0])
        # Check if we reached the target node
        if current_node[0] == target_node or (not llm and result2 in target_node):
            path=path + [(current_node, "reached", target_node)]
            return len(path)-1, path

        # Query outgoing links from the current node
        
        stoa=f""" {SPARQL_PREFIX} 
        SELECT distinct ?next_node ?predicate  ?label ?plabel ?pdesc  WHERE {{
             <{current_node[0]}> ?predicate ?next_node .
               ?next_node rdfs:label ?label .
                   ?next_node rdfs:label ?label .

        BIND(IRI(REPLACE(STR(?predicate), "^.*/(P\\\\d+)$", "http://www.wikidata.org/entity/$1")) as ?property)
        
        # Language filter for English labels
        FILTER(LANG(?label) = "en")
        
        # Filter out wiki page links
        FILTER(?predicate != <http://dbpedia.org/ontology/wikiPageWikiLink>)
        
        # Get predicate labels and descriptions
        SERVICE wikibase:label {{ 
            bd:serviceParam wikibase:language "en" .
            ?predicate rdfs:label ?plabel .
            ?property schema:description ?pdesc .
        }} 
        }} limit 500
        """
        sparql.setQuery(stoa)
        sparql.setReturnFormat(JSON)
        try:
            results = sparql.query().convert()
            if isinstance(results, bytes):  # Decode if necessary
                results = loads(results.decode("utf-8"))
        except Exception as e:
            LOGGER.error(f"Error querying SPARQL endpoint: {e}")
            print_exc() 
            continue
        lista=[]
        lista2=[]
        dicta={}
        dictar={}
        rlista=[]
        dicta11[current_node[0]]=start_node_raw
        dicta11[target_node]=target_node_raw
        # Process each outgoing link and add it to the queue if not visited
        if results.get("results") and results["results"].get("bindings"):
            for result in results["results"]["bindings"]:
                next_node = result["next_node"]["value"]
                predicate = result["predicate"]["value"]
                lab = result['label']["value"]
                lab2 = result['pdesc']["value"]
                dicta33[predicate]=lab2
                dictar[lab]=next_node
                dicta22[next_node]=lab
                dicta[next_node]=predicate
         
                # Append to the path and add to the queue
                
                if is_english_only(next_node) and next_node not in visited  and 'Category' not in next_node and 'Template' not in next_node:
                    rlista.append(dicta22[next_node])
                    lista.append(next_node)
                    lista2.append(predicate+" "+next_node)
            

            dicta22[start_node]=start_node_raw
              
        if lista.__len__()>1:
            epel=3
            toyl=lista.__len__()
            if toyl>6 and toyl<=12:
                epel=11
            elif toyl>12:
                epel=toyl-1 if llm else 11
            else:
                epel=toyl-1

            if llm:
                # stringas="do not insert δικους σου nodes αλλα επελεξε ακριβως "+str(epel)+" αν ειναι διαθεσιμoi απο την "+str(lista)+" αυτους που πλησιαζουν πιο πολυ  α΄΄΄΄λλα και αλλους που θα μπορουσαν πιο πιθανα να οδηγησουν στον κομβο  "+target_node+" επελεξε συνολικα +"+str(epel)+"και δωσε τους ενα σκορ εγγυτητας με τρια δεκαδικα. εαν δεν πλησιαζει πολυ δωσε σκορ κατω απο 0.4. Αν πλησιζει πολυ δωσε πανω απο 0.7. Επελεξε τους κομβους με τα μεγαλυτερα σκορ. Επισης μην επιλεξεις nodes που αναφερονται σε γενικες κατηγοριες αλλα μονο σε υπαρκτα entities. Return them  as string of entities. An entity is node comma score. Score is from 0.0 for irrelevant to target to 1 .if the node includes the word of the target, return as a score 1.0 .Do not comment scores.If target node is exacly found in list give it score 500.0. Final string is entity#entity#entity etc mean seperate entities with without headers # Return plain string.Αν δεν ειναι διαθεσιμοι 6 κομβοι δεν πειραζει και ΜΗΝ ΔΗΜΙΟΥΡΓΗΣΕΙΣ ΚΟΜΒΟΥΣ ΑΠΟ ΤΗΝ ΔΙΚΗ ΣΟΥ ΓΝΩΣΗ που δεν υπαρχουν στην λιστα. ΑΚΟΜΑ ΚΑΙ ΕΝΑΣ ΝΑ ΕΙΝΑΙ Ο ΚΟΜΒΟΣ ΕΠΕΣΤΡΕΨΕ ΤΟΝ"
                stringas=claude_message(epel, lista, target_node)
                message = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=1000,
                    temperature=0,
                    system="You are a DBPEDIA SPECIALIST",
                    messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": stringas
                                    }
                                ]
                            }
                        ]
                )
                response=message.content[0].text
            else:
                si=target_node
                si1=si.rsplit('/', 1)[-1]
                si1=si1.replace("_"," ")
                si1=target_node_raw
                oka=""
                prf=""           
                loa=[]
                for l in lista:
                    last_part=l
                    last_part2=dicta22[l]
                    word_entity_sim = get_entity_similarity(si1, last_part2, model, embedding_type=embedding_type)
                    LOGGER.info(f"Similarity between {si1} and {last_part2}: {word_entity_sim}")
                    if word_entity_sim is not None:
                        oka=oka+prf+last_part+","+str(word_entity_sim)+"#"
                        lss=[prf+last_part,float(word_entity_sim)]
                        loa.append(lss)
                        
                oka=''
                apa=0
                # Sort in descending order based on the second element (similarity score)
                sorted_data = sorted(loa, key=lambda x: x[1], reverse=True)
                
                # Print sorted list
                for item in sorted_data:
                    a1=item[0]
                    a2=item[1]
                    oka=oka+a1+","+str(a2)+"#"
                    if apa==epel:
                        break
                    apa=apa+1

                oka=oka.rstrip()
                response=oka
            ra=response
            ra=ra.replace('\n','')

            if llm:
                for ll in rlista:
                    ra=ra.replace(ll,dictar[ll])
            
            tups=ra.split('#')
            
            if lista:
                for ft in tups:
                    try:
                        sco=ft.split(',')
                        if len(sco) <= 1:
                            continue
                        sco[0]=sco[0].replace(' ','')
                        sco[0]=sco[0].replace('\'','')
                        sco[1]=sco[1].replace('\'','')
        
                        position=-1
                        if sstart==0:
                            
                            position=0
                            sstart=1
                            queue.insert(position,(sco, path + [(current_node, dicta[sco[0]], sco)]))
                        else:          
                            i=0  
                            
                            while True:
                                if i>=queue.__len__():
                                    break
                                a,_=queue[i]
                                try:
                                    if float(a[1])<float(sco[1]):
                                            position=i
                                            break
                                    
                                    
                                except Exception as e:
                                    LOGGER.error(f"An error occurred: {e}")
                                    print_exc() 
                                    break
                                    
                                i=i+1 
                            if i>=len(queue):
                                position=len(queue)-1
                                
                            if position!=-1:
                                queue.insert(position,(sco, path + [(current_node, dicta[sco[0]], sco)]))
                    except Exception as e:
                        LOGGER.error(f"An error occurred: {e}")
                        print_exc() 
                        
    # If queue exhausts without finding target
    return 0, []