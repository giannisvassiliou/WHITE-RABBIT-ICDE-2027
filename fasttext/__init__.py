import os
from gensim.models import KeyedVectors
from gensim.downloader import load

from utils.logger import LOGGER


def load_data():
    try:
        path = os.path.join('fasttext', "fasttext-wiki-news-subwords-300.gz")
        model = KeyedVectors.load_word2vec_format(path, binary=False)
        return model
    except FileNotFoundError:
        LOGGER.info(F"fasttext-wiki-news-subwords-300.gz not found. Downloading...")
        return load('fasttext-wiki-news-subwords-300')
