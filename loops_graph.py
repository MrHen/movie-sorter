from loops import run_fix_multi_loop
import networkx as nx
from functools import reduce
from rankings import ranked_to_key
from bubble import run_bubble_sorting
from memo import reverse_memo


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


def reverse_edge(graph, left, right):
    if graph.has_edge(left, right):
        loser, winner = left, right
    elif graph.has_edge(right, left):
        loser, winner = right, left
    else:
        print(f"reverse_edge couldn't find {left} <<< {right}")
        print(f"reverse_edge couldn't find {right} <<< {left}")
        return
    graph.remove_edge(loser, winner)
    graph.add_edge(winner, loser)


def set_edge(graph, left, right):
    if not graph.has_edge(left, right):
        graph.add_edge(left, right)
    if graph.has_edge(right, left):
        graph.remove_edge(right, left)


def graph_to_loops(
    *,
    rankings,
    graph,
    cutoff=2,
    max_loops=1,
    verbose=False,
):
    graph_loops = list()
    for ranking in rankings:
        ranking_key = ranked_to_key(ranking)
        paths = nx.single_source_shortest_path(graph, ranking_key, cutoff=cutoff)
        path_keys = set(paths.keys())
        pred_keys = set(graph.predecessors(ranking_key))
        loop_keys = pred_keys & path_keys
        ranking_loops = list()
        for loop_key in loop_keys:
            loop = paths[loop_key] + [ranking_key]
            if verbose:
                print(' << '.join(loop))
            ranking_loops.append(loop)
        if ranking_loops:
            print(f'{ranking_key} has {len(ranking_loops)} loops')
            graph_loops.extend(ranking_loops)
            if len(graph_loops) >= max_loops:
                # TODO just make this a generator...
                break
    return graph_loops


def fix_graph(
    *,
    graph=None,
    memo,
    ranking_worst_to_best,
    cutoff=2,
    max_loops=1,
    max_segments=20,
    verbose=False,
):
    if not graph:
        graph = memo_to_graph(memo)
    fix = True
    fix_count = 0
    while fix:
        print("Finding next batch of loops...")
        ranking_best_to_worst = list(reversed(ranking_worst_to_best))
        loops = graph_to_loops(
            graph=graph,
            rankings=ranking_best_to_worst,
            cutoff=cutoff,
            max_loops=max_loops,
            verbose=verbose,
        )
        if loops:
            print(f"\n{len(loops)} segments\n")
            fix = run_fix_multi_loop(
                loops,
                # movie_key=ranking_key,
                max_segments=max_segments,
                # sort_key=sort_key,
                # sort_reversed=sort_reversed,
            )
        else:
            fix = False
        if fix:
            fix_count += 1
            reverse_memo(memo, fix["left"], fix["right"])
            reverse_edge(graph, fix["left"], fix["right"])
            run_bubble_sorting(memo, ranking_worst_to_best)
    return fix_count
