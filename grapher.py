# First networkx library is imported 
# along with matplotlib
import networkx as nx
import matplotlib.pyplot as plt

class GraphVisualization:
    def __init__(self):
        # visual is a list which stores all 
        # the set of edges that constitutes a
        # graph
        self.visual = []

    # addEdge function inputs the vertices of an
    # edge and appends it to the visual list
    def addEdge(self, a, b):
        temp = [a, b]
        self.visual.append(temp)

    # In visualize function G is an object of
    # class Graph given by networkx G.add_edges_from(visual)
    # creates a graph with a given list
    # nx.draw_networkx(G) - plots the graph
    # plt.show() - displays the graph
    def visualize(self):
        G = nx.Graph()
        G.add_edges_from(self.visual)
        nx.draw_networkx(G)
        plt.show()

def edges_from_combinations(combinations):
    pass

#####
# VIS
#####

# rankingsByKey = {
#     ranked_to_key(ranking): ranking
#     for ranking in rankingWorstToBest
# }
# ranking_key = "Toy Story (1995)"

# comparisons = build_comparisons(memo)

# edges = [
#     [
#         list(comparison)[0],
#         list(comparison)[1],
#     ]
#     for comparison in list(memo)[:100]
# ]

# import networkx as nx
# import matplotlib.pyplot as plt
# G = nx.Graph()
# G.add_edges_from(edges)
# nx.draw_networkx(G)
# plt.show()

from functools import reduce
from pprint import pprint
from tarjan import tarjan


def memo_to_graph(acc, item):
    key, winner = item
    key_parts = list(key)
    loser = key_parts[1] if key_parts[0] == winner else key_parts[0]
    if winner not in acc:
        acc[winner] = list()
    acc[winner].append(loser)
    return acc

movie_key = 'Elephant (2003)'
memo_graph = reduce(memo_to_graph, memo.items(), dict())

# g = {1:[2],2:[1,5],3:[4],4:[3,5],5:[6],6:[7],7:[8],8:[6,9],9:[]}

t = tarjan(memo_graph)

for value in t:
    print(len(value))

# https://en.wikipedia.org/wiki/Feedback_arc_set