import os
from gensim.models import KeyedVectors
from gensim.downloader import load

from utils.logger import LOGGER

def load_data():
    try:
        path = os.path.join('word2vec', "word2vec-google-news-300.gz")
        model = KeyedVectors.load_word2vec_format(path, binary=True)
        return model
    except FileNotFoundError:
        LOGGER.info(F"word2vec-google-news-300.gz not found. Downloading...")
        return load('word2vec-google-news-300')

