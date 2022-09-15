from itertools import groupby
from operator import itemgetter
from pprint import pprint
from textwrap import dedent

import constants
from bubble import bubble_pass, run_bubble_sorting
from files import reload_all, reload_diary, run_search, save_all
from labels import build_movie_label
from lists import create_weighted_list, do_lists_match, load_list, load_list_names, print_list_comparison, write_file_parts
from loops import run_fix_all_loops, run_fix_loop
from loops_graph import fix_graph
from memo import (add_memo, analyze_memo, clear_memo, load_memo, print_memo,
                  reverse_memo)
from prompt import prompt_for_segments, trunc_string
from rankings import ranked_to_key
from ratings import rating_cmp, rating_sorter, rating_to_key
from tags import (group_diaries_by_month, group_diary_by_tag,
                  rank_diary_by_subject, group_rankings_by_decade, run_rank_by_subject)

base_dir = constants.BASE_DIR

memo = {}
# DON'T OVERWRITE THIS
# DON'T OVERWRITE THIS
memoFile = f"{base_dir}/memo.csv"
with open(memoFile, 'r', encoding='UTF-8') as file:
    memo = load_memo(file)
# DON'T OVERWRITE THIS

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
# ratingCurve = {
#     "0.5": 0.02,
#     "1": 0.05,
#     "1.5": 0.08,
#     "2": 0.11,
#     "2.5": 0.14,
#     "3": 0.17,
#     "3.5": 0.18,
#     "4": 0.13,
#     "4.5": 0.08,
#     "5": 0.04,
# }
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


def build_decade_grouping(
    *,
    ranking_worst_to_best,
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
    rankingBestToWorst = list(reversed(ranking_worst_to_best))
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


def run_group_sorting(ratingsUnsorted):
    ratingsGroup = {
        k: {
            "rating": k,
            "movies": sorted(g, key=itemgetter("Name")),
        }
        for k, g in groupby(ratingsUnsorted, key=itemgetter("Rating"))
    }
    # RUN GROUP SORTING
    rankedByRating = {}
    for rating in stars_worst_to_best:
        print(f"\nStarting {rating} block...")
        items = ratingsGroup[rating]["movies"]
        itemsRanked = sorted(items, key=rating_cmp(memo))
        rankedByRating[rating] = itemsRanked
    # POST GROUP SORTING
    rankingWorstToBest = []
    for rating in stars_worst_to_best:
        if rating in rankedByRating:
            rankingWorstToBest.extend(rankedByRating[rating])
    return rankingWorstToBest


def run_missing_insert(memo, ratings_unsorted, ranking_worst_to_best, insert=True):
    ratings_by_key = {
        rating_to_key(rating): rating
        for rating in ratings_unsorted
    }
    rankings_by_key = {
        ranked_to_key(ranking): ranking
        for ranking in ranking_worst_to_best
    }
    rating_keys = frozenset(ratings_by_key.keys())
    ranking_keys = frozenset(rankings_by_key.keys())
    missing_keys = rating_keys - ranking_keys
    for missing_key in missing_keys:
        missing_movie = ratings_by_key[missing_key]
        missing_index = run_search(memo, ranking_worst_to_best, missing_movie)
        if insert:
            ranking_worst_to_best.insert(missing_index, missing_movie)
    run_bubble_sorting(memo, ranking_worst_to_best, verbose=False)



def run_fix_memo(memo, rating_key, rankingsByKey=None):
    original = rankingsByKey[rating_key]
    results = analyze_memo(memo, rating_key)
    lower_than = results["lower_than"]
    lower_than = sorted([
        # build_movie_label(rankingsByKey.get(movie_key, movie_key))
        movie_key
        for movie_key in lower_than
    ], reverse=True)
    lower_than = [
        {
            "left": movie_label,
            # "right": build_movie_label(original),
            "right": rating_key,
            "count": 1,
            "pos": lower_than.index(movie_label),
        } 
        for movie_label in lower_than
    ]
    higher_than = results["higher_than"]
    higher_than = sorted([
        # build_movie_label(rankingsByKey.get(movie_key, movie_key))
        movie_key
        for movie_key in higher_than
    ], reverse=True)
    higher_than = [
        {
            # "left": build_movie_label(original),
            "left": rating_key,
            "right": movie_label,
            "count": 1,
            "pos": len(lower_than) + higher_than.index(movie_label),
        } 
        for movie_label in higher_than
    ]
    segments = [
        *lower_than,
        *higher_than,
    ]
    response = prompt_for_segments(segments)
    fix = segments[response]
    reverse_memo(memo, fix["left"], fix["right"])


# RELOAD
data = reload_all(base_dir=base_dir)
ratings_unsorted = data["ratings"]
ranking_worst_to_best = data["rankings"]
diary_entries = data["diary_entries"]


# INSERT MISSING RATINGS
run_missing_insert(memo, ratings_unsorted, ranking_worst_to_best)


# UPDATE DIARY
pprint(sorted(reload_diary(
    memo=memo,
    diary_entries=diary_entries,
    stars_worst_to_best=stars_worst_to_best,
    rating_curve=rating_curve,
    ranking_worst_to_best=ranking_worst_to_best,
)))


# SAVE
save_all(
    rankings_worst_to_best=ranking_worst_to_best,
    stars_worst_to_best=stars_worst_to_best,
    rating_curve=rating_curve,
    base_dir=base_dir,
    memo=memo,
    memo_file=memoFile,
)


# FIX LOOPs
ranking_best_to_worst = list(reversed(ranking_worst_to_best))
fix_graph(
    memo=memo,
    rankings=ranking_best_to_worst,
    cutoff=2,
    max_segments=20,
    max_loops=100,
)

ranking_best_to_worst = list(reversed(ranking_worst_to_best))
run_fix_all_loops(
    ranking_worst_to_best=ranking_worst_to_best,
    memo=memo,
    rankings=ranking_best_to_worst,
    max_depth=3,
    max_segments=20,
    max_loops=100,
    # max_loops=None,
    # sort_key="count",
    # sort_reversed=True,
)


ranking_best_to_worst = list(reversed(ranking_worst_to_best))
run_fix_all_loops(
    ranking_worst_to_best=ranking_worst_to_best,
    memo=memo,
    rankings=ranking_best_to_worst,
    max_depth=4,
    max_loops=None,
    max_segments=20,
    sort_key="count",
    sort_reversed=True,
)

# BUBBLE
changes = True
while changes:
    for step in range(2, 20, 1):
        print(f"starting pass with step={step}")
        changes = True
        while changes:
            print("...bubble pass")
            ranking_best_to_worst = list(reversed(ranking_worst_to_best))
            changes = bubble_pass(
                memo,
                ranking_worst_to_best,
                step=step,
                do_swap=False,
                max_changes=1,
                reverse=True,
                verbose=False,
                use_label=True,
            )
            print("...fix loops")
            fix_graph(
                memo=memo,
                rankings=ranking_best_to_worst,
                cutoff=2,
                max_segments=20,
                max_loops=100,
            )
            run_bubble_sorting(memo, ranking_worst_to_best)


# LOOP MEMO
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in ranking_worst_to_best
}
loop_memo_key = "Incredibles 2 (2018)"
print_memo(memo, loop_memo_key, rankingsByKey)
results = analyze_memo(memo, loop_memo_key, rankingsByKey)
left = list(sorted(results["lower_than"], key=itemgetter("Position")))[0]
right = list(sorted(results["higher_than"], key=itemgetter("Position")))[-1]
rating_sorter(left, right, memo)


# RUN GROUP SORTING
ranking_worst_to_best = run_group_sorting(ratings_unsorted)
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in ranking_worst_to_best
}


# DECADE GROUPING
count_min = 10
count_max = 25
decades_best_to_worst = build_decade_grouping(ranking_worst_to_best=ranking_worst_to_best)
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
    """
))


# PRINT COMPARISON
largestCount = 0
largestKey = None
largestDict = dict()
for keys, comparison in memo.items():
    for key in keys:
        largestDict[key] = largestDict.get(key, 0) + 1
        if largestDict[key] > largestCount:
            largestCount = largestDict[key]
            largestKey = key

print_memo(memo, largestKey)


# REINSERT
key_to_reinsert = "The Girl Who Leapt Through Time (2006)"

ranking_best_to_worst = list(reversed(ranking_worst_to_best))
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in ranking_worst_to_best
}
ranking_to_reinsert = rankingsByKey[key_to_reinsert]
if ranking_to_reinsert:
    index = len(ranking_worst_to_best) - ranking_to_reinsert["Position"]
    if ranking_worst_to_best[index]["Key"] == key_to_reinsert:
        del ranking_worst_to_best[index]
        print(f"deleting {key_to_reinsert}")
    else:
        print(f"missing {key_to_reinsert}")

clear_memo(memo, key_to_reinsert)
run_missing_insert(ratings_unsorted, ranking_worst_to_best)


# UTILS
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in ranking_worst_to_best
}

clear_memo(memo, "The Girl Who Leapt Through Time (2006)")
reverse_memo(memo, "Naqoyqatsi (2002)", "Powaqqatsi (1988)")
print_memo(memo, "Kung Fu Panda (2008)", rankingsByKey)
print_memo(memo, "Toy Story (1995)", rankingsByKey)

add_memo(rankingsByKey, "Candyman (1992)", "Candyman (2021)", verbose=True)

run_fix_memo(
    memo,
    "How to Train Your Dragon 2 (2014)",
    rankingsByKey,
)
run_fix_loop(
    ranking_worst_to_best=ranking_worst_to_best,
    memo=memo,
    ranking=rankingsByKey["The Good Dinosaur (2015)"],
    max_depth=5,
)

# TODO
# Eternal Sunshine of the Spotless Mind (2004)
# Toy Story (1995)
# Finding Nemo

###
# LIST MANIP
###
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


merged = create_weighted_list(list_data=list_data, tag="stats-tracker")
write_file_parts(movies=merged, filename="stats_combo")

"""
removeBatch = async function (size, timeout=200) {
    removes = Array.from(document.getElementsByClassName('list-item-remove'));
    removes = removes.splice(-size).reverse();
    for (const remove of removes) {
        console.log(remove);
        remove.click();
        await new Promise(r => setTimeout(r, timeout));
    }
    console.log("Done.");
}
removeBatch(500);
"""


###
# SUBJECTS
###
entries_by_tag = group_diary_by_tag(diary_entries=diary_entries)
tags = set(entries_by_tag.keys()) - set(["ignore-ranking", "profile", "to-review"])
tags = sorted(tags)
run_rank_by_subject(
    memo=memo,
    ranking_worst_to_best=ranking_worst_to_best,
    entries_by_subject=entries_by_tag,
    subjects=tags,
)

entries_by_month = group_diaries_by_month(diary_entries=diary_entries)
months = sorted(set(entries_by_month.keys()))
run_rank_by_subject(
    memo=memo,
    ranking_worst_to_best=ranking_worst_to_best,
    entries_by_subject=entries_by_month,
    subjects=months[-3:],
)

movies_by_decade = group_rankings_by_decade(ranking_worst_to_best=ranking_worst_to_best)
decades = sorted(set(movies_by_decade.keys()))
run_rank_by_subject(
    memo=memo,
    ranking_worst_to_best=ranking_worst_to_best,
    entries_by_subject=movies_by_decade,
    subjects=decades,
)

###
# TAG LISTS
###
entries_by_tag = group_diary_by_tag(diary_entries=diary_entries)

target_tag = "marathon-pixar"
target_tag = "marathon-leprechaun"
target_tag = "marathon-highlander"
target_tag = "marathon-tarantino"
target_tag = "movie-club"

target_tag_entries = rank_diary_by_subject(
    memo=memo,
    ranking_worst_to_best=ranking_worst_to_best,
    entries_by_subject=entries_by_tag,
    target_subject=target_tag,
)

print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in target_tag_entries
]))

run_fix_all_loops(
    ranking_worst_to_best=ranking_worst_to_best,
    memo=memo,
    rankings=target_tag_entries,
    max_depth=3,
)


###
# MONTHLY LISTS
###
entries_by_month = group_diaries_by_month(diary_entries=diary_entries)

months = sorted(set(entries_by_month.keys()))
target_month = months[-2]

target_month_entries = rank_diary_by_subject(
    memo=memo,
    ranking_worst_to_best=ranking_worst_to_best,
    entries_by_subject=entries_by_month,
    target_subject=target_month,
    # use_position=True,
)

print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in target_month_entries
]))

run_fix_all_loops(
    ranking_worst_to_best=ranking_worst_to_best,
    memo=memo,
    rankings=target_month_entries,
    max_depth=3,
    max_segments=20,
    max_loops=100,
    # max_loops=None,
    # sort_key="count",
    # sort_reversed=True,
)


# PRINT DELTAS
delta_targets = target_tag_entries
delta_targets = target_month_entries

ranking_best_to_worst = list(reversed(ranking_worst_to_best))
delta_targets = ranking_best_to_worst

rankedDeltas = filter(lambda x: x.get("RatingDelta", True), delta_targets)
for movie in rankedDeltas:
    if movie.get('RatingPrev', 0) < movie.get('RatingCurr', 0):
        delta = '▲'
    elif movie.get('RatingPrev', 0) > movie.get('RatingCurr', 0):
        delta = '▼'
    else:
        delta = ' '
    label = build_movie_label(movie, position_prefix=delta)
    print(f"{label}\t changed from {movie.get('RatingPrev', '-')}\t to {movie.get('RatingCurr', '-')}")
