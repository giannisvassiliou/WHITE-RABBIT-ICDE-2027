from utils.enums import EmbeddingType, ResourceType
from utils.utils import load_model, timeout
from sys import argv
from argparse import ArgumentParser

parser = ArgumentParser(
    prog='The White Rabbit',
    description='Test our algorithm along with various others to make the comparison.',
    epilog='Outputs the metrics extracted from the selected algorithm.'
)

def import_datasets():
    print("Loading the datasets. This may take a while...")
    import algorithms.dbpedia as dbpedia
    import algorithms.wikidata as wikidata
    import algorithms.yago as yago
    return {
        "DBPEDIA": dbpedia,
        "1": dbpedia,
        "WIKIDATA": wikidata,
        "2": wikidata,
        "YAGO": yago,
        "3": yago
    }

def main():
    nodes = []
    with open("config/nodes.conf") as f:
        nodes = list(node.strip() for node in f.readlines())
        nodes.sort()
    if not argv[1:]:
        print("Welcome to the White Rabbit demo.")
        print("Here you can test our algorithm along with various others to make the comparison.")
        source, target = "", ""
        entities = "\n\t".join(f"{i+1}. {nodes[i]}" for i in range(len(nodes)))
        try:
            sel = input(f"\t{entities}\n\nSelect two of the above nodes with their number separated with a whitespace.\nAlternatively you can put your own node names separated with a whitespace: ")
            selections = tuple(sel.split(" "))
            s_i, t_i = int(selections[0]), int(selections[1])
            source, target = nodes[s_i-1], nodes[t_i-1]
        except IndexError:
            print(f"Invalid input {sel}. You need to type two numbers in [1,60] or string")
            return
        except ValueError:
            source, target = s_i, t_i
        ds = input("Select one of the following datasets:\n\t1. DBPEDIA\n\t2. WIKIDATA\n\t3. YAGO\n\nSelect them with either their number or name: ")
        DATASETS = import_datasets()
        dataset = None
        try:    
            dataset = DATASETS[ds.upper()]
        except KeyError as e:
            print(f"Invalid input: {e}")
            return
        
        alg = input("Select one of the following algorithms to test:\n\t1. The White Rabbit\n\t2. Query Expansion\n\t" \
                    "3. Embedding\n\t4. LLM\n\nSelect them with either their number or name: ")
        algorithm = None
        embedding = None
        if(alg.upper() in ["1", "The White Rabbit"]):
            algorithm = dataset.white_rabbit
        elif(alg.upper() in ["2", "Query Expansion"]):
            algorithm = dataset.query_expansion
        elif(alg.upper() in ["3", "Embedding"]):
            algorithm = dataset.embedding

            emb = input("Select one of the following embeddings:\n\t1. WORD2VEC\n\t2. FASTTEXT\n\t" \
                    "3. SBERT\n\nSelect them with either their number or name: ")
            try:
                embedding = EmbeddingType(int(emb) if emb.isnumeric() else emb)
            except ValueError:
                embedding = EmbeddingType[emb.upper()]
        elif(alg.upper() in ["4", "LLM"]):
            algorithm = dataset.llm
        else:
            print(f"Invalid algorithm: {alg}")
            return
        
        acc = input("(Optional) Select an accuracy threshold between 0 and 0.99: ")
        if acc and not acc.isspace():
            try:
                accuracy_threshold = float(acc)
                if(accuracy_threshold < 0 or accuracy_threshold > 1):
                    raise ValueError()
            except ValueError:
                print(f"Invalid input: {acc}. Changing to default threshold (=1)")
                accuracy_threshold = 1
        else:
            accuracy_threshold = 1
        
        tm = input("(Optional) Select a timeout in seconds: ")
        if tm and not tm.isspace():
            try:
                timeout_seconds = int(tm)
            except ValueError:
                print(f"Invalid input: {tm}. Changing to default timeout (=0 s)")
                timeout_seconds = 0
        else:
            timeout_seconds = 0
    else:
        global parser
        parser.add_argument('source', help="The source node")
        parser.add_argument('target', help="The target node")
        parser.add_argument('dataset', choices=[r.name for r in ResourceType], help="The dataset you want to use")
        parser.add_argument('algorithm', choices=["white-rabbit", "query-expansion", "embedding", "llm"], help="The algorithm you want to test")
        parser.add_argument('-e', '--embedding', required=False, default=None, choices=[e.name for e in EmbeddingType], help="The embedding you want to use. Only works if you chose 'embedding' as an algorithm")
        parser.add_argument('-t', '--timeout', required=False, default=0, help="The optional timeout in seconds. If 0, no timeout is applied")
        parser.add_argument('-a', '--accuracy-threshold', required=False, default=1, help="The optional accuracy threshold accepted. Must be a float in (0, 1]")

        arguments = parser.parse_args()
        source: str = arguments.source
        target: str = arguments.target
        DATASETS = import_datasets()
        dataset = DATASETS[arguments.dataset.upper()]
        alg: str = arguments.algorithm
        embedding = arguments.embedding
        if(alg.lower() in ["wr", "white-rabbit"]):
            algorithm = dataset.white_rabbit
        elif(alg.lower() in ["qe", "query-expansion"]):
            algorithm = dataset.query_expansion
        elif(alg.lower() == "embedding"):
            algorithm = dataset.embedding
            if not embedding:
                print("'embedding' algorithm requires argument '-e', '--embedding'")
                return
            embedding = EmbeddingType[embedding]
        elif(alg.lower() == "llm"):
            algorithm = dataset.llm

        acc = arguments.accuracy_threshold
        try:
            accuracy_threshold = float(acc)
            if(accuracy_threshold <= 0 or accuracy_threshold > 1):
                raise ValueError()
        except ValueError:
            print(f"Invalid accuracy: {acc}. Must be a float in (0, 1]")
            return
        
        tm = arguments.timeout 
        try:
            timeout_seconds = int(tm)
        except ValueError:
            print(f"Invalid timeout: {tm}. Changing to no timeout.")
            timeout_seconds = 0
    inputs = (source, target, accuracy_threshold) if not embedding else (source, target, embedding, accuracy_threshold)
    print("Inputs: ")
    print(f"\tSource: {source}")
    print(f"\tTarget: {target}")
    print(f"\tDataset: {dataset.__name__}")
    print(f"\tAlgorithm: {algorithm.__name__}")
    if embedding:
        print(f"\tEmbedding: {embedding}")
    print(f"\tAccuracy Threshold: {accuracy_threshold}")
    print(f"\tTimeout in {timeout_seconds} seconds.")
    print("Starting the algorithm...")
    if timeout_seconds:
        time, length, pc, ta, path = timeout(algorithm, inputs, embedding_type=embedding or EmbeddingType.WIKI2VEC, timeout=timeout_seconds)
    else:
        embedding_type=embedding or EmbeddingType.WIKI2VEC
        model = load_model(embedding_type)
        time, length, pc, ta, path = algorithm(model, *inputs)
    if not length:
        print("Algorithm timed out and/or no valid path was found. Try a different source-target pair or increase the timeout.")
    else:
        print(f"Algorithm finished in {time} seconds.")
        print(f"Path Length: {length}")
        print(f"Path Coherence: {pc}")
        print(f"Target Affiliation: {ta}")
        print(f"Path:")
        for p in path:
            print(f"{p[0]} ------> {p[1]} ------> {p[2]}")



if __name__ == "__main__":
    main()