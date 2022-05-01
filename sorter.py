import csv

from textwrap import dedent
from pprint import pprint
from itertools import groupby
from operator import itemgetter

import constants
from dairy import line_to_key, load_diary

from bubble import run_bubble_sorting, bubble_pass
from memo import add_memo, analyze_memo, clear_memo, load_memo, print_memo, reverse_memo, write_memo
from labels import build_movie_label
from rankings import load_rankings, ranked_to_key, write_rankings
from ratings import load_ratings, rating_sorter, rating_to_key, rating_cmp
from prompt import prompt_for_loop, prompt_for_segments, prompt_for_winner
from thresholds import build_description, build_thresholds

baseDir = constants.BASE_DIR

memo = {}
# DON'T OVERWRITE THIS
# DON'T OVERWRITE THIS
memoFile = f"{baseDir}/memo.csv"
with open(memoFile, 'r') as file:
    memo = load_memo(file)
# DON'T OVERWRITE THIS

starsWorstToBest = [
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
ratingCurve = {
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
sum(ratingCurve.values())


def write_metadata(file, description):
    fieldnames = ["Date", "Name", "Tags", "URL", "Description"]
    metadata = {
        "Date": "2021-10-05",
        "Name": "Ranked",
        "Tags": None,
        "URL": "https://boxd.it/dB32m",
        "Description": description,
    }
    writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerow(metadata)


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


def aggregate_comparisons(comparisons, key, max_seen=10):
    finished = set()
    queue = {key}
    while queue:
        if max_seen < 0:
            break
        max_seen -= 1
        curr_key = queue.pop()
        if curr_key in finished:
            continue
        finished.add(curr_key)
        next_keys = comparisons.get(curr_key, None)
        for next_key in next_keys:
            if next_key not in finished and next_key not in queue:
                print(f"{curr_key}\t >>> {next_key}")
                queue.add(next_key)
    finished.remove(key)
    return finished.union(queue)
    # comparisons['higher_than_key']['Yi Yi (2000)']
    # pprint(aggregate_comparisons(comparisons['higher_than_key'], 'Yi Yi (2000)', max_seen=10))


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


def build_cascade(higher, lower, memoKey):
    remaining = {memoKey}
    finished = set()
    while remaining:
        currKey = remaining.pop()
        if currKey in finished:
            continue
        finished.add(currKey)


def build_decade_grouping(
    *,
    rankingWorstToBest,
    count_min=10,
    count_max=25,
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
    rankingBestToWorst = list(reversed(rankingWorstToBest))
    rankingsByDecade = sorted(rankingBestToWorst, key=itemgetter("Decade", "Position"))
    count_min = 10
    count_max = 25
    decadesBestToWorst = {
        k: {
            "decade": k,
            "movies": [
                movie
                for movie in g
                if movie["Rating"] not in ignoreStars
            ][:count_max],
        }
        for k, g in groupby(rankingsByDecade, key=itemgetter("Decade"))
        if len(g) >= count_min
    }
    return decadesBestToWorst


def fix_loop(memo, loop, delimiter="<<"):
    fix = prompt_for_loop(loop, delimiter)
    reverse_memo(memo, loop[fix-1], loop[fix])


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
    for rating in starsWorstToBest:
        print(f"\nStarting {rating} block...")
        items = ratingsGroup[rating]["movies"]
        itemsRanked = sorted(items, key=rating_cmp(memo))
        rankedByRating[rating] = itemsRanked
    # POST GROUP SORTING
    rankingWorstToBest = []
    for rating in starsWorstToBest:
        if rating in rankedByRating:
            rankingWorstToBest.extend(rankedByRating[rating])
    return rankingWorstToBest


def run_search(rankingWorstToBest, movie):
    left = 0
    right = len(rankingWorstToBest) - 1
    while left <= right:
        curr = (left + right) // 2
        curr_movie = rankingWorstToBest[curr]
        comp_result = rating_sorter(movie, curr_movie, memo)
        print(f"Searching... {left}|{curr}|{right} -> {comp_result}")
        if comp_result == 1:
            left = curr + 1
        elif comp_result == -1:
            right = curr - 1
        else:
            return curr
    return curr


def run_missing_insert(ratingsUnsorted, rankingWorstToBest, insert=True):
    ratingsByKey = {
        rating_to_key(rating): rating
        for rating in ratingsUnsorted
    }
    rankingsByKey = {
        ranked_to_key(ranking): ranking
        for ranking in rankingWorstToBest
    }
    ratingKeys = frozenset(ratingsByKey.keys())
    rankingKeys = frozenset(rankingsByKey.keys())
    missingKeys = ratingKeys - rankingKeys
    for missingKey in missingKeys:
        missingMovie = ratingsByKey[missingKey]
        missingIndex = run_search(rankingWorstToBest, missingMovie)
        if insert:
            rankingWorstToBest.insert(missingIndex, missingMovie)


def run_fix_multi_loop(
    loops_higher_than,
    memo,
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
    reverse_memo(memo, fix["left"], fix["right"])


def run_fix_first_loop(memo, rankings, max_depth=3):
    loops_higher_than = True
    while loops_higher_than:
        print("Finding next loop...")
        comparisons = build_comparisons(memo)
        for ranking in rankings:
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
                run_fix_multi_loop(
                    loops_higher_than,
                    memo,
                    movie_key=movie_key,
                )
                run_bubble_sorting(memo, rankingWorstToBest)
                break


def run_fix_all_loops(
    memo,
    rankings,
    max_depth=3,
    max_loops=10,
    max_segments=10,
    sort_key="pos",
    sort_reversed=False,
):
    all_loops = True
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
            run_fix_multi_loop(
                all_loops,
                memo,
                movie_key=first_ranking_key,
                max_segments=max_segments,
                sort_key=sort_key,
                sort_reversed=sort_reversed,
            )
            run_bubble_sorting(memo, rankingWorstToBest)


def run_fix_loop(memo, ranking, max_depth=3):
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
            run_fix_multi_loop(loops_higher_than, memo, movie_key=movie_key)
            run_bubble_sorting(memo, rankingWorstToBest)


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


def reload_all(*, base_dir):
    # LOAD RATINGS
    ratingsFile = f"{base_dir}/ratings.csv"
    with open(ratingsFile, 'r') as file:
        ratingsUnsorted = load_ratings(file)
    # LOAD RANKINGS
    rankingsFile = f"{base_dir}/rankings.csv"
    with open(rankingsFile, 'r') as file:
        rankingsBestToWorst = load_rankings(file, ratingsUnsorted)
    rankingWorstToBest = list(reversed(rankingsBestToWorst))
    # LOAD DIARY
    rankingsFile = f"{base_dir}/diary.csv"
    with open(rankingsFile, 'r') as file:
        diary_entries = load_diary(file)
    return {
        "ratings": ratingsUnsorted,
        "rankings": rankingWorstToBest,
        "diary_entries": diary_entries,
    }


def reload_diary(
    *,
    stars_worst_to_best,
    rating_curve,
    ranking_worst_to_best,
    diary_entries,
):
    # PREP THRESHOLDS
    rankingBestToWorst = list(reversed(ranking_worst_to_best))
    totalRated = len(rankingBestToWorst)
    rankingThresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, totalRated)
    # LOAD DIARY
    ignore_diary_keys = frozenset({
        "Anima (2019)",
        "Squid Game (2021)",
        "Who Killed Captain Alex? (2010)",
    })
    diary_by_key = {
        line_to_key(entry): entry
        for entry in diary_entries
    }
    diary_keys = frozenset(diary_by_key.keys())
    ranking_keys = frozenset([
        line_to_key(movie)
        for movie in ranking_worst_to_best
    ])
    missing_keys = diary_keys - ranking_keys - ignore_diary_keys
    output = []
    for missing_key in missing_keys:
        missing_movie = diary_by_key[missing_key]
        position = run_search(ranking_worst_to_best, missing_movie)
        position = len(ranking_worst_to_best) - position
        for threshold in rankingThresholds:
            if threshold > position:
                threshold_label = rankingThresholds[threshold]
                print(f"AAA {threshold} vs {position} => {threshold_label}")
                break
        output.append(f"{missing_key} => {position} as {threshold_label}")
    return output


def save_all(
    *,
    rankings_worst_to_best,
    stars_worst_to_best,
    rating_curve,
    base_dir,
    memo,
):
    # PREP THRESHOLDS
    rankingBestToWorst = list(reversed(rankings_worst_to_best))
    totalRated = len(rankingBestToWorst)
    rankingThresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, totalRated)
    rankedDescription = build_description(rankingThresholds)
    print(rankedDescription)
    # APPLY THRESHOLDS
    ratingCurr = 5
    for i in range(0, len(rankingBestToWorst)):
        item = rankingBestToWorst[i]
        position = i + 1
        description = rankingThresholds.get(position, None)
        item["Position"] = position
        item["Description"] = description
        item["RatingCurr"] = str(ratingCurr)
        item["RatingPrev"] = item["Rating"]
        item["RatingDelta"] = ratingCurr - float(item["Rating"])
        if description:
            ratingCurr -= 0.5
    # SAVE OUTPUT
    rankedOutput = [
        {
            "Position": movie["Position"],
            "Name": movie["Name"],
            "Year": movie["Year"],
            "URL": movie["Letterboxd URI"],
            "Description": movie["Description"],
        }
        for movie in rankingBestToWorst
    ]
    rankingsFile = f"{base_dir}/rankings.csv"
    with open(rankingsFile, 'w', newline='') as file:
        # write_metadata(file, rankedDescription)
        # file.write("\n")
        write_rankings(file, rankedOutput)
    # SAVE MEMO
    if memo:
        with open(memoFile, 'w', newline='') as file:
            write_memo(file, memo)


# RELOAD
data = reload_all(base_dir=baseDir)
ratingsUnsorted = data["ratings"]
rankingWorstToBest = data["rankings"]
diary_entries = data["diary_entries"]


# INSERT MISSING RATINGS
run_missing_insert(ratingsUnsorted, rankingWorstToBest)


# RUN BUBBLE SORTING
run_bubble_sorting(memo, rankingWorstToBest, verbose=False)


# UPDATE DIARY
pprint(sorted(reload_diary(
    diary_entries=diary_entries,
    stars_worst_to_best=starsWorstToBest,
    rating_curve=ratingCurve,
    ranking_worst_to_best=rankingWorstToBest,
)))


# SAVE
save_all(
    rankings_worst_to_best=rankingWorstToBest,
    stars_worst_to_best=starsWorstToBest,
    rating_curve=ratingCurve,
    base_dir=baseDir,
    memo=memo,
)


# FIX LOOPs
rankingBestToWorst = list(reversed(rankingWorstToBest))
run_fix_all_loops(
    memo,
    rankingBestToWorst,
    max_depth=3,
    max_segments=20,
    max_loops=100,
    # max_loops=None,
    # sort_key="count",
    # sort_reversed=True,
)

rankingBestToWorst = list(reversed(rankingWorstToBest))
run_fix_all_loops(
    memo,
    rankingBestToWorst,
    max_depth=4,
    max_loops=None,
    max_segments=20,
    sort_key="count",
    sort_reversed=True,
)


# BUBBLE
rankingBestToWorst = list(reversed(rankingWorstToBest))
changes = True
while changes:
    for step in range(2, 20, 1):
        print(f"starting pass with step={step}")
        changes = True
        while changes:
            changes = bubble_pass(
                memo,
                rankingWorstToBest,
                step=step,
                do_swap=False,
                max_changes=1,
                reverse=True,
                verbose=False,
            )
            run_fix_all_loops(
                memo,
                rankingBestToWorst,
                max_depth=3,
                max_segments=20,
                max_loops=100,
                # max_loops=None,
                # sort_key="count",
                # sort_reversed=True,
            )


# LOOP MEMO
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}
loop_memo_key = "Incredibles 2 (2018)"
print_memo(memo, loop_memo_key, rankingsByKey)
results = analyze_memo(memo, loop_memo_key, rankingsByKey)
left = list(sorted(results["lower_than"], key=itemgetter("Position")))[0]
right = list(sorted(results["higher_than"], key=itemgetter("Position")))[-1]
rating_sorter(left, right, memo)


# RUN GROUP SORTING
rankingWorstToBest = run_group_sorting(ratingsUnsorted)
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}


# DECADE GROUPING
count_min = 10
decadesBestToWorst = build_decade_grouping(rankingWorstToBest=rankingWorstToBest)
for decade in decadesBestToWorst:
    movies = decadesBestToWorst[decade]["movies"]
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
key_to_reinsert = "Oldboy (2003)"

rankingBestToWorst = list(reversed(rankingWorstToBest))
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}
ranking_to_reinsert = rankingsByKey[key_to_reinsert]
if ranking_to_reinsert:
    index = len(rankingWorstToBest) - ranking_to_reinsert["Position"]
    if rankingWorstToBest[index]["Key"] == key_to_reinsert:
        del rankingWorstToBest[index]
        print(f"deleting {key_to_reinsert}")
    else:
        print(f"missing {key_to_reinsert}")

clear_memo(memo, key_to_reinsert)
run_missing_insert(ratingsUnsorted, rankingWorstToBest)


# UTILS
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}

clear_memo(memo, "Mean Girls (2004)")
reverse_memo(memo, "Leprechaun: Origins (2014)", "Leprechaun: Back 2 tha Hood (2003)")
print_memo(memo, "Annihilation (2018)", rankingsByKey)
print_memo(memo, "Toy Story (1995)", rankingsByKey)

add_memo(rankingsByKey, "Candyman (1992)", "Candyman (2021)", verbose=True)

run_fix_memo(
    memo,
    "How to Train Your Dragon 2 (2014)",
    rankingsByKey,
)
run_fix_loop(
    memo,
    rankingsByKey["The Good Dinosaur (2015)"],
    max_depth=5,
)

# TODO
# Eternal Sunshine of the Spotless Mind (2004)
# Toy Story (1995)
# Finding Nemo

###
# TAG LISTS
###
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}
entries_by_tags = {
    k: sorted(g, key=itemgetter("Key"))
    for k, g in groupby(
        sorted(
            [
                {
                    "Key": entry.get("Key"),
                    "Tag": tag,
                }
                for entry in diary_entries
                if entry.get("Tags")
                for tag in entry.get("Tags")
            ],
            key=itemgetter("Tag")
        ),
        key=itemgetter("Tag"),
    )
}

target_tag = "marathon-tarantino"
target_tag = "marathon-pixar"
target_tag = "marathon-leprechaun"
target_tag = "marathon-highlander"
target_tag_entries = sorted(
    [
        rankingsByKey.get(entry["Key"], entry)
        for entry in entries_by_tags[target_tag]
    ],
    key=rating_cmp(memo),
    reverse=True,
)

print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in target_tag_entries
]))

run_fix_all_loops(
    memo,
    target_tag_entries,
    max_depth=3,
)


###
# MONTHLY LISTS
###
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}
entries_by_month = {
    k: sorted(g, key=itemgetter("Key"))
    for k, g in groupby(
        sorted(
            [
                entry
                for entry in diary_entries
                if entry.get("Watched Month")
                if "ignore-ranking" not in (entry.get("Tags") or [])
            ],
            key=itemgetter("Watched Month")
        ),
        key=itemgetter("Watched Month"),
    )
}

target_month = "2022-03"
target_month_entries = [
    rankingsByKey.get(entry["Key"], entry)
    for entry in entries_by_month[target_month]
]
target_month_entries = sorted(
    target_month_entries,
    # key=rating_cmp(memo),
    # reverse=True,
    key=itemgetter("Position")
)

print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in target_month_entries
]))

run_fix_all_loops(
    memo,
    target_month_entries,
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

rankingBestToWorst = list(reversed(rankingWorstToBest))
delta_targets = rankingBestToWorst

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

