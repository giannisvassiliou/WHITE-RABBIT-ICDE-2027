from itertools import permutations
from random import choices

def create_random_pairs(exclude: set=set(), filename: str="", size: int=20):
    with open("config/nodes.conf") as f:
        nodes = set(node.strip() for node in f.readlines())
        perms = list(set(permutations(nodes, 2)) - exclude)

        pairs = choices(perms, k=size)
        if filename:
            with open(filename, "w") as fp:
                fp.writelines([f"{pair[0]}, {pair[1]}\n" for pair in pairs])
        return pairs

if __name__ == "__main__":
    create_random_pairs(filename="config/pairs.conf")