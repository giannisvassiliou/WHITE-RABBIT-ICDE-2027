# The White Rabbit

This code is part of paper **"White Rabbit: Escaping the Online KG Rabbit Hole Using Embeddings"**

## Abstract
The proliferation of Knowledge Graphs (KGs) in recent years has resulted in the generation of massive datasets now available online. Exploring these graphs to identify meaningful connections between entities is a valuable, yet challenging task. This is mainly due to the large size, the complexity, and the limited interfaces (i.e., SPARQL endpoints) they offer for their online exploration. In this paper, we focus on discovering high-quality paths between two entities in online KGs, using embeddings. First, we introduce the problem of context-aware path finding, which results into coherent paths including highly relevant entities.  Then, we introduce the White Rabbit, an approach that involves scoring entity neighbors using embeddings, prioritizing exploration through a queue-based mechanism, and iteratively refining the search process. We compare our approach with baselines including structural methods, various pretrained embedding methods, and a large language model oracle, showing the benefits of our approach in optimizing both the efficiency of the task and the quality of the retrieved paths.

## How to Run
### Requirements
1. **Python 3.10.x** or above
2. **python-venv**
3. **Windows 10, 11 or Linux**
### Steps
1. Download the [WIKI2VEC model](http://wikipedia2vec.s3.amazonaws.com/models/en/2018-04-20/enwiki_20180420_100d.pkl.bz2). Unpack it and put it in the project's root directory. Feel free to rename it as you please.
2. Create a **.env** file with the following content: 
```dotenv
WIKI2VEC_MODEL=<the_name_of_the_file_you_downloaded_on_step_1>
CLAUDE_MODEL=claude-3-5-sonnet-20241022
WORD2VEC_MODEL=word2vec-google-news-300
FASTTEXT_MODEL=fasttext-wiki-news-subwords-300
SBERT_MODEL=all-mpnet-base-v2
ANTHROPIC_API_KEY=<your_anthropic_api_key>
```
> **NOTE:** The **ANTHROPIC_API_KEY** is only needed for the 'llm' algorithm. If you do not intend to test that algorithm, you may disregard this environmental variable.
3. Create a python environment with `python3 -m venv venv`.
4. `pip install -r requirements.txt`
5. To run the program by inserting the parameters from the console, run `python3 main.py`. Otherwise, run `python3 main.py -h` or `python3 main.py --help` and see how to insert the parameters from the command line.

> **NOTE:** File [nodes.conf](config/nodes.conf) contains some example entities that were used to test and run the algorithms. Feel free to use them as source/target nodes or enrich it as you please, making sure they are existing entities.