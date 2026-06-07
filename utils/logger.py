"""
Contains a logger to monitor app logs and errors
"""
from logging import getLogger, DEBUG, StreamHandler, Formatter
from sys import stdout

LOGGER = getLogger(__name__)
LOGGER.setLevel(DEBUG)

__streamHandler = StreamHandler(stream=stdout)
__streamHandler.setLevel(DEBUG)
__streamHandler.setFormatter(Formatter('%(levelname)s:\t  %(message)s'))

LOGGER.addHandler(__streamHandler)