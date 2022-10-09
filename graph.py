from functools import reduce

import networkx as nx

from memo import set_memo


def memo_to_edges(acc, item):
    key, winner = item
    key_parts = list(key)
    loser = key_parts[1] if key_parts[0] == winner else key_parts[0]
    if not acc:
        acc = list()
    acc.append([loser, winner])
    return acc


def memo_to_graph(memo):
    edges = reduce(memo_to_edges, memo.items(), list())
    graph = nx.DiGraph()
    graph.add_edges_from(edges)
    return graph


def graph_to_memo(graph, memo=None, verbose=False):
    memo = memo or {}
    for edge in graph.edges():
        set_memo(memo, edge[0], edge[1], verbose=verbose)
    return memo


def reverse_edge(graph, left, right):
    if graph.has_edge(left, right):
        loser, winner = left, right
    elif graph.has_edge(right, left):
        loser, winner = right, left
    else:
        print(f"reverse_edge couldn't find {left} <<< {right}")
        print(f"reverse_edge couldn't find {right} <<< {left}")
        return
    print(f"Flipped\t {winner}\t over {loser}")
    graph.remove_edge(loser, winner)
    graph.add_edge(winner, loser)


def set_edge(graph, left, right):
    if not graph.has_edge(left, right):
        graph.add_edge(left, right)
    if graph.has_edge(right, left):
        graph.remove_edge(right, left)
