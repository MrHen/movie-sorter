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

import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from functools import reduce

def memo_to_edges(acc, item):
    key, winner = item
    key_parts = list(key)
    loser = key_parts[1] if key_parts[0] == winner else key_parts[0]
    if not acc:
        acc = list()
    acc.append([winner, loser])
    return acc

edges = reduce(memo_to_edges, memo.items(), list())

graph = nx.DiGraph()
graph.add_edges_from(edges)

memo_key = "Barry Lyndon (1975)"
memo_key = "I Am Legend (2007)"
memo_key = "(500) Days of Summer (2009)"
memo_key = "Toy Story (1995)"
for node in graph.successors(memo_key):
    pprint(node)
    pprint(graph.has_edge(memo_key, node))
    pprint(graph.has_edge(node, memo_key))

for node in graph.predecessors(memo_key):
    pprint(node)
    pprint(graph.has_edge(memo_key, node))
    pprint(graph.has_edge(node, memo_key))

pprint(list(graph.successors(memo_key)))
pprint(list(graph.predecessors(memo_key)))

# nx.draw_networkx(graph)
# plt.show()

for connected in nx.strongly_connected_components(graph):
    print(f'scc. len={len(connected)}')
    if len(connected) <= 1:
        continue
    subgraph = graph.subgraph(connected)
    for biconnected in nx.biconnected_components(subgraph.to_undirected()):
        print(f'bc. len={len(biconnected)}')
    break

cycles = nx.simple_cycles(subgraph)
cycle = next(cycles)
pprint(cycle)

for cycle in nx.simple_cycles(subgraph):
    print(f'cycle. {cycle[0]}\t ={len(cycle)}=>\t {cycle[-1]}')


working_graph = subgraph.subgraph(cycle)
for cycle in nx.simple_cycles(working_graph):
    print(f'cycle. {cycle[0]}\t ={len(cycle)}=>\t {cycle[-1]}')


nx.minimum_edge_cut(working_graph)


chordal, alpha = nx.complete_to_chordal_graph(graph.to_undirected())
for clique in nx.chordal_graph_cliques(graph.to_undirected()):
    pprint(clique)

node_connectivity = nx.all_pairs_node_connectivity(subgraph)

#
# TARJAN
#
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



### CYCLE FIX?

from loops import run_fix_multi_loop
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from functools import reduce
from itertools import islice

def memo_to_edges(acc, item):
    key, winner = item
    key_parts = list(key)
    loser = key_parts[1] if key_parts[0] == winner else key_parts[0]
    if not acc:
        acc = list()
    acc.append([loser, winner])
    return acc

edges = reduce(memo_to_edges, memo.items(), list())

graph = nx.DiGraph()
graph.add_edges_from(edges)

for connected in nx.strongly_connected_components(graph):
    print(f'scc. len={len(connected)}')
    if len(connected) <= 1:
        continue
    subgraph = graph.subgraph(connected)
    for biconnected in nx.biconnected_components(subgraph.to_undirected()):
        print(f'bc. len={len(biconnected)}')


cycles = list(nx.chain_decomposition(subgraph))

cycles = [
    [*cycle, cycle[0]]
    for cycle in sorted(islice(nx.simple_cycles(subgraph), 100), key=len)
]
pprint(cycles[0])

run_fix_multi_loop(
    cycles[:20],
    memo,
    movie_key=cycles[0][0],
)


###

min_connected = None
min_connected_value = None

for connected in nx.strongly_connected_components(subgraph):
    print(f'scc. len={len(connected)}')
    if len(connected) == 1:
        continue
    if min_connected_value is None or len(connected) < min_connected:
        min_connected_value = len(connected)
        min_connected = connected

nx.is_strongly_connected(graph.subgraph(min_connected))

rejected_nodes = set(random.sample(min_connected, len(min_connected) // 2))
accepted_nodes = min_connected - rejected_nodes

nx.is_strongly_connected(graph.subgraph(accepted_nodes))

for connected_2 in nx.strongly_connected_components(graph.subgraph(accepted_nodes)):
    print(f'scc. len={len(connected_2)}')

cycles = [
    [*cycle, cycle[0]]
    for cycle in sorted(islice(nx.simple_cycles(graph.subgraph(accepted_nodes)), 1000), key=len)
]


### Connected

from loops import run_fix_multi_loop
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from functools import reduce
from itertools import islice
from graph import memo_to_graph

graph = memo_to_graph(memo)

scc_counter = 0
scc_max = 200

connected_list = []
for connected in nx.strongly_connected_components(graph):
    print(f'scc. f{scc_counter}. len={len(connected)}')
    connected_list.append(connected)
    if len(connected) > 1:
        break
    scc_counter += 1

movie_key = 'Elephant (2003)'
