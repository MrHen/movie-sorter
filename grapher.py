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

### CHUNK RATINGS

from loops import run_fix_multi_loop
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from functools import reduce
from itertools import islice
import random

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

ranking_best_to_worst = list(reversed(ranking_worst_to_best))
top_100 = [
    ranking['Key']
    for ranking in ranking_best_to_worst[:100]
]

subgraph = graph.subgraph(top_100)

cycles = [
    [*cycle, cycle[0]]
    for cycle in sorted(islice(nx.simple_cycles(subgraph), 1000), key=len)
]
pprint(cycles[:1])

run_fix_multi_loop(
    cycles,
    memo,
    movie_key=cycles[0][0],
    max_segments=20,
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



### LOOPS vs GRAPH


from loops import run_fix_multi_loop
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint
from functools import reduce
from itertools import islice
import random
from rankings import ranked_to_key
from bubble import run_bubble_sorting
from memo import reverse_memo, set_memo
from loops_graph import memo_to_graph, memo_to_edges, graph_to_loops, fix_graph, set_edge, reverse_edge
from prompt import prompt_for_winner, prompt_for_loop, prompt_for_segments
import math

memo_key = 'Spirited Away (2001)'
memo_key = 'Dr. Dolittle 2 (2001)'
memo_key = 'Elephant (2003)'

ranking_best_to_worst = list(reversed(ranking_worst_to_best))

graph = memo_to_graph(memo)

child_nodes = nx.dfs_preorder_nodes(graph, memo_key, depth_limit=2)
child_graph = graph.subgraph(child_nodes)
cycles = nx.simple_cycles(child_graph)
pprint(next(cycles))

child_edges = nx.dfs_edges(graph, memo_key, depth_limit=2)
child_graph = graph.edge_subgraph()


child_nodes = list(nx.dfs_preorder_nodes(graph, memo_key, depth_limit=2))
triadic_census = nx.triadic_census(graph, child_nodes)
pprint(triadic_census)

child_nodes = nx.dfs_preorder_nodes(graph, memo_key, depth_limit=2)
child_graph = graph.subgraph(child_nodes)
chordal, alpha = nx.complete_to_chordal_graph(child_graph.to_undirected())

chordal.remove_edges_from(child_graph.edges)


ranking_graph = nx.DiGraph()
one_key = None
two_key = None
for three in ranking_worst_to_best:
    three_key = three["Key"]
    if two_key:
        ranking_graph.add_edge(two_key, three_key)
    if one_key:
        one_three = frozenset([one_key, three_key])
        if one_three in memo:
            winner = memo[one_three]
            loser = one_key if winner == three_key else three_key
            # print(f'{loser} << {winner}')
            ranking_graph.add_edge(loser, winner)
    one_key = two_key
    two_key = three_key


nx.is_chordal(ranking_graph.to_undirected())
ranking_chordal, alpha = nx.complete_to_chordal_graph(ranking_graph.to_undirected())
ranking_chordal.remove_edges_from(ranking_graph.edges)

triadic_census = nx.triadic_census(ranking_graph)
pprint(triadic_census)

triads_by_type = nx.triads_by_type(ranking_graph)


graph = memo_to_graph(memo)
loops = True
while loops:
    loops = graph_to_loops(
        graph=graph,
        rankings=ranking_best_to_worst,
        cutoff=3,
        max_loops=1,
    )
    if not loops:
        break
    loop = loops[0]
    print(' << '.join(loop))
    if len(loop) == 4:
        print('BBB')
        fix = run_fix_multi_loop([loop])
        if fix:
            reverse_memo(memo, fix["left"], fix["right"])
            reverse_edge(graph, fix["left"], fix["right"])
            run_bubble_sorting(memo, ranking_worst_to_best)
    elif len(loop) > 4:
        print('CCC')
        hit = True
        left = 0
        right = len(loop) - 1
        while hit:
            mid = math.ceil((right - left) / 2)
            left_key = loop[left]
            mid_key = loop[mid]
            hit = graph.has_edge(left_key, mid_key) or graph.has_edge(mid_key, left_key)
            # print(f'{left} : {mid} : {right} => {hit}')
            right = mid - 1
        winner = prompt_for_winner(left_key, mid_key)
        loser = left_key if mid_key == winner else mid_key
        print(f'setting {loser} << {winner}')
        set_memo(memo, loser, winner)
        set_edge(graph, loser, winner)
    print('DDD')
    fix_graph(
        graph=graph,
        memo=memo,
        ranking_worst_to_best=ranking_worst_to_best,
        cutoff=2,
        max_segments=20,
        max_loops=100,
    )


nx.shortest_path(graph, left_key, mid_key)
nx.shortest_path(graph, mid_key, left_key)
