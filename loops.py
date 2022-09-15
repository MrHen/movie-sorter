

from operator import itemgetter
from bubble import run_bubble_sorting
from labels import build_movie_label
from memo import reverse_memo
from prompt import prompt_for_loop, prompt_for_segments
from rankings import ranked_to_key


def build_comparisons(memo):
    higher_than_key = dict()
    lower_than_key = dict()
    for keys, winner in memo.items():
        keys = list(keys)
        a_key = keys[0]
        b_key = keys[1]
        if a_key == winner:
            higher = a_key
            lower = b_key
        else:
            higher = b_key
            lower = a_key
        if lower not in higher_than_key:
            higher_than_key[lower] = set()
        if higher not in lower_than_key:
            lower_than_key[higher] = set()
        higher_than_key[lower].add(higher)
        lower_than_key[higher].add(lower)
    return {
        "higher_than_key": higher_than_key,
        "lower_than_key": lower_than_key,
    }


def find_comparison_loops(comparisons, curr_key, path=None, max_depth=10):
    loops = []
    if max_depth <= 0:
        return loops
    path = path or tuple()
    path = (*path, curr_key,)
    next_keys = comparisons.get(curr_key, [])
    for next_key in next_keys:
        if next_key == path[0]:
            loops.append((*path, next_key,))
        else:
            loops.extend(find_comparison_loops(
                comparisons,
                next_key,
                path=tuple(path),
                max_depth=max_depth-1,
            ))
    return loops


def run_fix_multi_loop(
    loops_higher_than,
    movie_key=None,
    sort_key="pos",
    sort_reversed=False,
    max_segments=None,
):
    loops = set()
    hits = dict()
    pairs = list()
    for loop in loops_higher_than:
        loop_keys = frozenset(loop)
        if loop_keys in loops:
            continue
        loops.add(loop_keys)
        left = None
        right = None
        for key in loop:
            if right:
                left = right
            if left:
                right = key
                pair = tuple([left, right])
                if pair not in pairs:
                    pairs.append(pair)
                hits[pair] = hits.get(pair, 0) + 1
            else:
                left = key
    segments = [
        {
            "left": pair[0],
            "right": pair[1],
            "count": count,
            "pos": pairs.index(pair),
        }
        for pair, count in hits.items()
    ]
    segments = sorted(segments, key=itemgetter(sort_key), reverse=sort_reversed)
    if max_segments:
        segments = segments[:max_segments]
    response = prompt_for_segments(segments, movie_key=movie_key)
    fix = segments[response]
    return fix


def run_fix_all_loops(
    *,
    ranking_worst_to_best,
    memo,
    rankings=None,
    max_depth=3,
    max_loops=10,
    max_segments=10,
    sort_key="pos",
    sort_reversed=False,
):
    all_loops = True
    saw_changes = False
    if not rankings:
        rankings = list(reversed(ranking_worst_to_best))
    while all_loops:
        print("Finding next batch of loops...")
        comparisons = build_comparisons(memo)
        all_loops = list()
        first_ranking = None
        for ranking in rankings:
            ranking_key = ranked_to_key(ranking)
            loops_higher_than = find_comparison_loops(
                comparisons['higher_than_key'],
                ranking_key,
                max_depth=max_depth,
            )
            if loops_higher_than:
                saw_changes = True
                first_ranking = first_ranking or ranking
                label = build_movie_label(ranking)
                print(f"Found {len(loops_higher_than)} loops for {label}")
                all_loops.extend(loops_higher_than)
                if max_loops and len(all_loops) > max_loops:
                    break
        if all_loops:
            first_ranking_key = ranked_to_key(first_ranking)
            label = build_movie_label(first_ranking)
            print(f"\n{len(all_loops)} segments starting at {label}\n")
            fix = run_fix_multi_loop(
                all_loops,
                movie_key=first_ranking_key,
                max_segments=max_segments,
                sort_key=sort_key,
                sort_reversed=sort_reversed,
            )
            reverse_memo(memo, fix["left"], fix["right"])
            run_bubble_sorting(memo, ranking_worst_to_best)
    return saw_changes


def run_fix_loop(
    *,
    ranking_worst_to_best,
    memo,
    ranking,
    max_depth=3,
):
    loops_higher_than = True
    while loops_higher_than:
        print("Finding next loop...")
        comparisons = build_comparisons(memo)
        ranking_key = ranked_to_key(ranking)
        loops_higher_than = find_comparison_loops(
            comparisons['higher_than_key'],
            ranking_key,
            max_depth=max_depth,
        )
        if loops_higher_than:
            movie_key = ranking["Key"]
            label = build_movie_label(ranking)
            print(f"{len(loops_higher_than)} loops for {label}\n")
            fix = run_fix_multi_loop(loops_higher_than, movie_key=movie_key)
            reverse_memo(memo, fix["left"], fix["right"])
            run_bubble_sorting(memo, ranking_worst_to_best)
