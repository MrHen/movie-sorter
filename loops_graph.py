import networkx as nx

from bubble import run_bubble_sorting
from graph import memo_to_graph, reverse_edge
from loops import run_fix_multi_loop
from memo import reverse_memo
from rankings import ranked_to_key


def node_to_loops(
    *,
    graph,
    node,
    cutoff=2,
    verbose=False,
):
    if not node:
        return list()
    if not graph.has_node(node):
        return list()
    paths = nx.single_source_shortest_path(graph, node, cutoff=cutoff)
    path_keys = set(paths.keys())
    pred_keys = set(graph.predecessors(node))
    loop_keys = pred_keys & path_keys
    ranking_loops = list()
    for loop_key in loop_keys:
        loop = paths[loop_key] + [node]
        if verbose:
            print(' << '.join(loop))
        ranking_loops.append(loop)
    return ranking_loops


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
        ranking_loops = node_to_loops(
            graph=graph,
            node=ranking_key,
            cutoff=cutoff,
            verbose=verbose,
        )
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
            print(f"\n{len(loops)} loops\n")
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
