from itertools import groupby
from pprint import pprint
from operator import itemgetter
from textwrap import dedent
from bubble import bubble_pass
from dairy import line_to_key
from files import load_diary_file, load_memo_file, load_rankings_file, load_ratings_file, reload_all, run_search, save_arc_data, save_hierarchy, write_memo_file, write_rankings_file
from graph import memo_to_graph
from labels import build_movie_label
from lists import create_weighted_list, do_lists_match, load_list, load_list_names, print_list_comparison, write_file_parts
from loops import run_fix_multi_loop
from loops_graph import graph_to_loops
from memo import clear_memo, print_memo, reverse_memo, set_memo
from rankings import ranked_to_key
from ratings import rating_cmp, rating_to_key
from tags import group_diary_by_tag
from thresholds import build_description, build_thresholds
import constants
import networkx as nx


memo = {}
rankings_worst_to_best = []
movies_by_key = {}

stars_worst_to_best = [
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
    "4",
    "4.5",
    "5",
]
# https://www.wolframalpha.com/input/?i=-0.08+x%5E3+%2B+0.7+x%5E2+%2B+1.3+x+%2B+0.1+for+x+between+1+and+10
rating_curve = {
    "0.5": 0.02,
    "1": 0.05,
    "1.5": 0.08,
    "2": 0.11,
    "2.5": 0.14,
    "3": 0.16,
    "3.5": 0.16,
    "4": 0.14,
    "4.5": 0.1,
    "5": 0.04,
}
sum(rating_curve.values())

def reset():
    # Need to clear / update in order to preserve the global reference
    memo.clear()
    memo.update(load_memo_file())


def reload():
    diary_entries = load_diary_file()
    ratings_unsorted = load_ratings_file()
    rankings_unsorted = load_rankings_file()
    ratings_by_key = {
        rating_to_key(rating): rating
        for rating in ratings_unsorted
    }
    rankings_by_key = {
        ranked_to_key(ranking): ranking
        for ranking in rankings_unsorted
    }
    diary_by_key = {
        line_to_key(entry): entry
        for entry in diary_entries
        if not movie_has_diary_tag(entry, 'ignore-ranking')
    }
    rating_keys = frozenset(ratings_by_key.keys())
    ranking_keys = frozenset(rankings_by_key.keys())
    diary_keys = frozenset(diary_by_key.keys())
    movie_keys = rating_keys | ranking_keys | diary_keys
    movies = {
        movie_key: {
            **ratings_by_key.get(movie_key, {}),
            **{
                key: diary_by_key.get(movie_key, {}).get(key, None)
                for key in diary_by_key.get(movie_key, {}).keys()
                if key in {'Watched Date', 'Watched Month', 'Tags'}
            },
            **{
                key: rankings_by_key.get(movie_key, {}).get(key, None)
                for key in rankings_by_key.get(movie_key, {}).keys()
                if key in {'Position'}
            },
            "Key": movie_key,
        }
        for movie_key in movie_keys
    }
    rankings = sorted([
        movie
        for movie in movies.values()
        if movie_has_ranking(movie)
    ], key=itemgetter("Position"), reverse=True)
    # Need to clear / update in order to preserve the global reference
    movies_by_key.clear()
    movies_by_key.update(movies)
    # Need to clear / extend in order to preserve the global reference
    rankings_worst_to_best.clear()
    rankings_worst_to_best.extend(rankings)


def movie_has_ranking(movie):
    return movie.get('Position', None) is not None


def movie_has_rating(movie):
    return movie.get('Rating', None) is not None


def movie_has_diary(movie):
    return movie.get('Watched Date', None) is not None


def movie_has_diary_tag(movie, tag):
    return tag in (movie.get('Tags', None) or [])


def movie_tags(*, movies_by_key=movies_by_key):
    return {
        tag
        for movie in movies_by_key.values()
        for tag in (movie.get('Tags', None) or [])
        if tag not in ["ignore-ranking", "profile", "to-review"]
    }


def movie_months(*, movies_by_key=movies_by_key):
    return {
        movie.get('Watched Month')
        for movie in movies_by_key.values()
        if movie.get('Watched Month')
    }


def build_decade_grouping(
    *,
    rankings_worst_to_best,
):
    ignoreStars = {
        "0.5",
        "1",
        "1.5",
        "2",
        "2.5",
        "3",
        "3.5",
    }
    rankingBestToWorst = list(reversed(rankings_worst_to_best))
    rankingsWithoutIgnored = filter(lambda movie: movie["Rating"] not in ignoreStars, rankingBestToWorst)
    rankingsByDecade = sorted(rankingsWithoutIgnored, key=itemgetter("Decade", "Position"))
    decadesBestToWorst = {
        k: {
            "decade": k,
            "movies": [
                movie
                for movie in g
                # if movie["Rating"] not in ignoreStars
            ],
        }
        for k, g in groupby(rankingsByDecade, key=itemgetter("Decade"))
    }
    return decadesBestToWorst


# SAVE
def rerank(
    *,
    rankings_worst_to_best,
    stars_worst_to_best,
    rating_curve,
):
    total_rated = len(rankings_worst_to_best)
    ranking_thresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, total_rated)
    ranking_description = build_description(ranking_thresholds)
    print(ranking_description)
    rating_curr = 5
    for i in range(0, len(rankings_worst_to_best)):
        movie = rankings_worst_to_best[total_rated - i - 1]
        position = i + 1
        description = ranking_thresholds.get(position, None)
        movie["Position"] = position
        movie["Description"] = description
        movie["RatingCurr"] = str(rating_curr)
        movie["RatingPrev"] = movie["Rating"]
        movie["RatingDelta"] = rating_curr - float(movie["Rating"])
        if description:
            rating_curr -= 0.5


def save_all(
    *,
    memo=memo,
    rankings_worst_to_best,
):
    rankings_best_to_worst = list(reversed(rankings_worst_to_best))
    rankings_output = [
        {
            "Position": movie["Position"],
            "Name": movie["Name"],
            "Year": movie["Year"],
            "LetterboxdURI": movie["Letterboxd URI"],
            "Description": movie["Description"],
        }
        for movie in rankings_best_to_worst
    ]
    write_rankings_file(rankings_output)
    write_memo_file(memo)


# UPDATE RANKINGS
def update_rankings(
    *,
    memo,
    movies_by_key,
    rankings_worst_to_best,
    verbose=False,
):
    missing_keys = {
        movie_key
        for movie_key, movie in movies_by_key.items()
        if movie_has_rating(movie) and not movie_has_ranking(movie)
    }
    for missing_key in missing_keys:
        missing_movie = movies_by_key[missing_key]
        missing_index = run_search(
            memo,
            rankings_worst_to_best,
            missing_movie,
            verbose=verbose,
        )
        rankings_worst_to_best.insert(missing_index, missing_movie)


# RATE DIARY ENTRIES
def update_diary(
    *,
    memo,
    movies_by_key,
    stars_worst_to_best,
    rating_curve,
    rankings_worst_to_best,
):
    total_rated = len(rankings_worst_to_best)
    ranking_thresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, total_rated)
    missing_keys = {
        movie_key
        for movie_key, movie in movies_by_key.items()
        if movie_has_diary(movie)
        if not movie_has_ranking(movie)
        if not movie_has_diary_tag(movie, 'ignore-ranking')
    }
    output = []
    for missing_key in missing_keys:
        missing_movie = movies_by_key[missing_key]
        position = run_search(memo, rankings_worst_to_best, missing_movie)
        position = len(rankings_worst_to_best) - position
        for threshold in ranking_thresholds:
            if threshold > position:
                threshold_label = ranking_thresholds[threshold]
                break
        output.append(f"{missing_key} => {position} as {threshold_label}")
    return output


# SORTING
def sort_movies(
    movies,
    *,
    memo=memo,
    verbose=True,
    reverse=True,
):
    changes = []
    result = sorted(
        movies,
        key=rating_cmp(memo, verbose=verbose, changes=changes),
        reverse=reverse,
    )
    return {
        "movies": result,
        "changes": changes,
    }


def sort_by_tag(
    *,
    target_tag,
    movies_by_key,
    memo,
    verbose=True,
    reverse=True,
):
    movies = [
        movie
        for movie in movies_by_key.values()
        if target_tag in (movie.get('Tags', None) or [])
    ]
    movies = sorted(movies, key=itemgetter("Watched Date"))
    result = sort_movies(
        movies,
        memo=memo,
        verbose=verbose,
        reverse=reverse,
    )
    return result


def sort_by_month(
    *,
    target_month,
    movies_by_key,
    memo,
    verbose=True,
    reverse=True,
):
    movies = [
        movie
        for movie in movies_by_key.values()
        if target_month == movie.get('Watched Month', None)
    ]
    movies = sorted(movies, key=itemgetter("Watched Date"))
    result = sort_movies(
        movies,
        memo=memo,
        verbose=verbose,
        reverse=reverse,
    )
    return result


# FIX SHORT CYCLES
def fix_adjacent(
    *,
    memo,
    rankings_worst_to_best,
    verbose=False,
):
    changes_memo = bubble_pass(
        memo,
        rankings_worst_to_best,
        # step=1,
        # do_swap=False,
        # max_changes=1,
        max_changes_memo=None,
        reverse=True,
        verbose=verbose,
        use_label=True,
    )
    return changes_memo


def fix_small_loop(
    *,
    memo,
    ranking_worst_to_best,
    verbose=False,
    max_segments=20,
):
    changes = []
    graph = memo_to_graph(memo)
    ranking_best_to_worst = list(reversed(ranking_worst_to_best))
    loops = graph_to_loops(
        graph=graph,
        rankings=ranking_best_to_worst,
        cutoff=2,
        max_loops=100,
        verbose=verbose,
    )
    if loops:
        change = fix_loops(
            memo=memo,
            verbose=verbose,
            max_segments=max_segments,
            loops=loops,
        )
        if change:
            changes.append(change)
    return changes


def fix_loops(*, memo, verbose, max_segments, loops):
    print(f"\n{len(loops)} segments\n")
    segment = run_fix_multi_loop(
            loops,
            # movie_key=ranking_key,
            max_segments=max_segments,
            # sort_key=sort_key,
            # sort_reversed=sort_reversed,
        )
    if segment:
        change = {
                "loser": segment["right"],
                "winner": segment["left"],
            }
        set_memo(memo, change["loser"], change["winner"], verbose=verbose)
        return change


# RUNNERS

def run_save(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
    stars_worst_to_best=stars_worst_to_best,
    rating_curve=rating_curve,
):
    rerank(
        rankings_worst_to_best=rankings_worst_to_best,
        stars_worst_to_best=stars_worst_to_best,
        rating_curve=rating_curve,
    )
    save_all(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )


def run_diary_update(
    *,
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
    rating_curve=rating_curve,
    stars_worst_to_best=stars_worst_to_best,
):
    update_rankings(
        memo=memo,
        movies_by_key=movies_by_key,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    results = sorted(update_diary(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
        rating_curve=rating_curve,
        stars_worst_to_best=stars_worst_to_best,
        movies_by_key=movies_by_key,
    ))
    run_save(
        rankings_worst_to_best=rankings_worst_to_best,
        stars_worst_to_best=stars_worst_to_best,
        rating_curve=rating_curve,
        memo=memo,
    )
    return results


def run_clean_up_gen(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
):
    print(f'\t... running fix_adjacent')
    changes = fix_adjacent(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    if not changes:
        print(f'\t... running fix_small_loop')
        changes = fix_small_loop(
            memo=memo,
            ranking_worst_to_best=rankings_worst_to_best,
        )
    changes = changes or []
    return (change for change in changes)


def run_clean_up(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
):
    total_changes = []
    saw_change = True
    while saw_change:
        print('Starting clean up...')
        saw_change = False
        changes = run_clean_up_gen(
            memo=memo,
            rankings_worst_to_best=rankings_worst_to_best,
        )
        for change in changes:
            print(f'\t\t... saw change to {change["winner"]} >>> {change["loser"]}')
            total_changes.append(change)
            saw_change = True
    return total_changes


def run_tags_gen(
    *,
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
    verbose=False,
):
    print(f'\t... running fix_adjacent')
    changes = fix_adjacent(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    if not changes:
        print(f'\t... running fix_small_loop')
        changes = fix_small_loop(
            memo=memo,
            ranking_worst_to_best=rankings_worst_to_best,
        )
    if not changes:
        tags = sorted(movie_tags())
        for tag in tags:
            print(f'\t... running sort_by_tag for {tag}')
            result = sort_by_tag(
                target_tag=tag,
                memo=memo,
                movies_by_key=movies_by_key,
                verbose=verbose,
            )
            changes = result['changes']
            if changes:
                break
    changes = changes or []
    return (change for change in changes)


def run_tags(
    *,
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
):
    total_changes = []
    saw_change = True
    while saw_change:
        print('Starting run_tags...')
        saw_change = False
        changes = run_tags_gen(
            memo=memo,
            movies_by_key=movies_by_key,
            rankings_worst_to_best=rankings_worst_to_best,
        )
        for change in changes:
            print(f'\t\t... saw change to {change["winner"]} >>> {change["loser"]}')
            total_changes.append(change)
            saw_change = True
    return total_changes


def run_months_gen(
    *,
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
    verbose=False,
):
    print(f'\t... running fix_adjacent')
    changes = fix_adjacent(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    if not changes:
        print(f'\t... running fix_small_loop')
        changes = fix_small_loop(
            memo=memo,
            ranking_worst_to_best=rankings_worst_to_best,
        )
    if not changes:
        months = sorted(movie_months())
        months = months[-2:]
        for month in months:
            print(f'\t... running sort_by_month for {month}')
            result = sort_by_month(
                target_month=month,
                memo=memo,
                movies_by_key=movies_by_key,
                verbose=verbose,
            )
            changes = result['changes']
            if changes:
                break
    changes = changes or []
    return (change for change in changes)


def run_months(
    *,
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
):
    total_changes = []
    saw_change = True
    while saw_change:
        print('Starting run_months...')
        saw_change = False
        changes = run_months_gen(
            memo=memo,
            movies_by_key=movies_by_key,
            rankings_worst_to_best=rankings_worst_to_best,
        )
        for change in changes:
            print(f'\t\t... saw change to {change["winner"]} >>> {change["loser"]}')
            total_changes.append(change)
            saw_change = True
    return total_changes


def run_rankings_batch_cycle_fixer(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
    verbose=False,
    max_segments=100,
    max_cycles=30,
    start=None,
):
    i = start or 1
    while i < len(rankings_worst_to_best):
        print(f"... starting {i}")
        cycles = set()
        segment = rankings_worst_to_best[-i:]
        graph = memo_to_graph(memo)
        subgraph = graph.subgraph([
            movie['Key']
            for movie in segment
        ])
        for cycle in nx.simple_cycles(subgraph):
            cycle = tuple([*cycle, cycle[0]])
            if cycle not in cycles:
                if verbose:
                    pprint(cycle)
                cycles.add(cycle)
                if len(cycles) >= max_cycles:
                    break
        if cycles:
            change = fix_loops(
                memo=memo,
                verbose=verbose,
                max_segments=max_segments,
                loops=cycles,
            )
            yield change
        else:
            change = None
        if not change:
            i += 1


def run_cycle_fixer_gen(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
):
    print(f'\t... running fix_adjacent')
    changes = fix_adjacent(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    if not changes:
        print(f'\t... running fix_small_loop')
        changes = fix_small_loop(
            memo=memo,
            ranking_worst_to_best=rankings_worst_to_best,
        )
    changes = changes or []
    return changes


def run_cycle_fixer(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
    verbose=False,
    start=None,
):
    total_changes = []
    saw_change = True
    batch_gen = None
    while saw_change:
        print('Starting run_cycle_fixer...')
        saw_change = False
        changes = run_cycle_fixer_gen(
            memo=memo,
            rankings_worst_to_best=rankings_worst_to_best,
        )
        if not changes:
            print('Starting run_rankings_batch_cycle_fixer...')
            batch_gen = batch_gen or run_rankings_batch_cycle_fixer(
                memo=memo,
                rankings_worst_to_best=rankings_worst_to_best,
                verbose=verbose,
                start=start,
            )
            change = next(batch_gen, None)
            changes = [change] if change else []
        for change in changes:
            print(f'\t\t... saw change to {change["winner"]} >>> {change["loser"]}')
            total_changes.append(change)
            saw_change = True
    return total_changes



### ONCE PER SHELL
reset()


### ONCE PER DIARY CYCLE
reload()
results = run_diary_update()
pprint(results)


### CLEAN UP
results = run_clean_up()
pprint(results)
run_save()


# FIX TOPICAL CYCLES
results = run_tags()
results = run_months()
pprint(results)
run_save()

# FIX EVERYTHING
run_cycle_fixer(verbose=False, start=240)
run_save()

#### UTILITIES

### PRINT MEMO

print_memo(memo, "Persepolis (2007)", movies_by_key)
reverse_memo(memo, "Persepolis (2007)", "Once Upon a Time in Mexico (2003)")
clear_memo(memo, "(500) Days of Summer (2009)")

### REINSERT

memo_key = "(500) Days of Summer (2009)"
movie = movies_by_key.get(memo_key, None)
if movie:
    index = len(rankings_worst_to_best) - movie["Position"]
    if rankings_worst_to_best[index]["Key"] == memo_key:
        del rankings_worst_to_best[index]
        print(f"deleting {memo_key}")
        movie["Position"] = None
        movie["Rating"] = None
    else:
        print(f"missing {memo_key}")


### PRINT BY TAG
target_tag = 'movie-club'
results = sort_by_tag(
    target_tag=target_tag,
    movies_by_key=movies_by_key,
    memo=memo,
)
print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in results['movies']
]))

months = sorted(movie_months())
target_month = months[-2]
results = sort_by_month(
    target_month=target_month,
    movies_by_key=movies_by_key,
    memo=memo,
)
print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in results['movies']
]))


### PRINT DELTAS

months = sorted(movie_months())
changable = months[-2:]

ranked_deltas = [
    movie
    for movie in rankings_worst_to_best
    if movie.get("RatingDelta", True)
]
for movie in reversed(ranked_deltas):
    if movie.get('Watched Month', None) in changable:
        edit_diary = '!'
    else:
        edit_diary = ' '
    if movie.get('RatingPrev', 0) < movie.get('RatingCurr', 0):
        delta = '▲'
    elif movie.get('RatingPrev', 0) > movie.get('RatingCurr', 0):
        delta = '▼'
    else:
        delta = ' '
    position_prefix = edit_diary + delta
    label = build_movie_label(movie, position_prefix=position_prefix)
    print(f"{label}\t changed from {movie.get('RatingPrev', '-')}\t to {movie.get('RatingCurr', '-')}")


#### SANDBOX

### SAVE DATA FOR CHARTS

months = sorted(movie_months())
target_month = months[-2]
results = sort_by_month(
    target_month=target_month,
    movies_by_key=movies_by_key,
    memo=memo,
)
graph = memo_to_graph(memo)
subgraph = graph.subgraph([movie["Key"] for movie in results['movies']])

graph = memo_to_graph(memo)
nodes = [movie["Key"] for movie in rankings_worst_to_best[-100:]]
subgraph = graph.subgraph(nodes)

save_hierarchy(
    graph=subgraph,
    base_dir=constants.BASE_DIR,
    ranking_worst_to_best=rankings_worst_to_best,
)
save_arc_data(
    graph=subgraph,
    base_dir=constants.BASE_DIR,
    ranking_worst_to_best=rankings_worst_to_best,
)


### DECADE LIST FIX

count_min = 10
count_max = 25
decades_best_to_worst = build_decade_grouping(rankings_worst_to_best=rankings_worst_to_best)
lists_by_decade = {}
for decade in decades_best_to_worst:
    movies = decades_best_to_worst[decade]["movies"][:count_max]
    if len(movies) >= count_min:
        lists_by_decade[decade] = movies
        print(decade)
        pprint([
            movie["Key"]
            for movie in movies
        ])

print(dedent(
    f"""
    <a href="https://letterboxd.com/mrhen/list/top-2010s">Top 2010s</a>
    <a href="https://letterboxd.com/mrhen/list/top-2000s">Top 2000s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1990s">Top 1990s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1980s">Top 1980s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1970s">Top 1970s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1960s">Top 1960s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1950s">Top 1950s</a>
    <a href="https://letterboxd.com/mrhen/list/top-1940s">Top 1940s</a>
    """
))

# 

list_names = load_list_names()
list_data = [
    load_list(list_name=list_name)
    for list_name in list_names
]

for i, list_datum in enumerate(list_data):
    print(f"{i}: {list_datum['metadata']['Name']}")

for decade, movies in lists_by_decade.items():
    decade_list = next(filter(lambda list_datum: f'top{decade}' in list_datum['metadata'].get('Tags', ''), list_data), None)
    if not decade_list:
        continue
    if do_lists_match(movies, decade_list['movies']):
        continue
    print(f'boo {decade}')
    print_list_comparison(movies, decade_list['movies'])

# COMBO LISTS

merged = create_weighted_list(list_data=list_data, tag="stats-combo")
write_file_parts(movies=merged, filename="stats_combo")

merged = create_weighted_list(list_data=list_data, tag="watchlist")
merged_unwatched = [
    movie
    for movie in merged
    if line_to_key(movie) not in movies_by_key
]
write_file_parts(movies=merged_unwatched[:500], filename="watchlist_combo")

"""
removeBatch = async function (size, timeout=200) {
    var startTime = performance.now()
    count = 0;
    removes = document.getElementsByClassName('list-item-remove');
    max_remove = removes.length;
    for (var count = 1; count <= size; count++) {
        if (removes.length <= 1) {
            break;
        }
        remove = removes[max_remove - count];
        console.log(count, removes.length, remove);
        remove.click();
        await new Promise(r => setTimeout(r, timeout));
    }
    var endTime = performance.now()
    var seconds = (endTime - startTime) / 1000;
    console.log("Done.", seconds, seconds / size);
}
removeBatch(500, 50);
"""

### STEP CYCLE FIXER

cycles = set()
max_cycles = 20
for i in range(1, len(rankings_worst_to_best)):
    if len(cycles) >= max_cycles:
        break
    print(f"... starting {i}")
    segment = rankings_worst_to_best[-i:]
    root = segment[0]["Key"]
    graph = memo_to_graph(memo)
    subgraph = graph.subgraph([
        movie['Key']
        for movie in segment
    ])
    for cycle in nx.simple_cycles(subgraph):
        cycle = tuple(cycle)
        if cycle not in cycles:
            pprint(cycle)
            cycles.add(cycle)
            if len(cycles) >= max_cycles:
                break

pprint(cycles)


segment = run_fix_multi_loop(
    cycles,
    # movie_key=ranking_key,
    # max_segments=100,
    # sort_key=sort_key,
    # sort_reversed=sort_reversed,
)
change = {
    "loser": segment["right"],
    "winner": segment["left"],
}
set_memo(memo, change["loser"], change["winner"])

