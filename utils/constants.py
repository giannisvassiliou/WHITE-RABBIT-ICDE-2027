from os import getenv

from utils.enums import ResourceType
from dotenv import load_dotenv

load_dotenv(override=True)

WIKI2VEC_MODEL = getenv("WIKI2VEC_MODEL", "model.pkl")
WORD2VEC_MODEL = getenv('WORD2VEC_MODEL', 'word2vec-google-news-300')
FASTTEXT_MODEL = getenv('FASTTEXT_MODEL', 'fasttext-wiki-news-subwords-300')
SBERT_MODEL = getenv('SBERT_MODEL', 'all-mpnet-base-v2')
CLAUDE_MODEL = getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
DBPEDIA_URL = "https://dbpedia.org/sparql"
DBPEDIA_RESOURCE_URL = "http://dbpedia.org/resource"
WIKIDATA_URL = "https://query.wikidata.org/sparql"
WIKIDATA_RESOURCE_URL = "http://www.wikidata.org/entity/"
YAGO_URL = "https://yago-knowledge.org/sparql/query."
YAGO_RESOURCE_URL="http://yago-knowledge.org/resource"
AGENT=getenv("AGENT", "MyWikidataBotPAATH/2.0 (giannis_vassiliou@yahoo.gr")
SPARQL_PREFIX = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  PREFIX schema: <http://schema.org/> PREFIX yago: <http://yago-knowledge.org/resource/>"
BASE_URLS = {
    ResourceType.DBPEDIA: DBPEDIA_URL,
    ResourceType.WIKIDATA: WIKIDATA_URL,
    ResourceType.YAGO: YAGO_URL
}
RESOURCE_URLS = {
    ResourceType.DBPEDIA: DBPEDIA_RESOURCE_URL,
    ResourceType.WIKIDATA: WIKIDATA_RESOURCE_URL,
    ResourceType.YAGO: YAGO_RESOURCE_URL
}
ACCEPTANCE_THRESHOLD=.9