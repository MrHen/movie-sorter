import csv
import math

from functools import cmp_to_key
from textwrap import dedent
from pprint import pprint
from itertools import groupby
from operator import itemgetter

baseDir = "C:/Users/babad/Source/movie-sorter"

def load_memo(file):
    # LeftKey,RightKey,Winner
    reader = csv.DictReader(file)
    comparisons = {
        frozenset({row["LeftKey"], row["RightKey"]}): (row["Winner"] or None)
        for row in reader
    }
    return comparisons


def load_ratings(file):
    reader = csv.DictReader(file)
    ratings = [
        {
            "Decade": row.get("Year", "")[0:3] + "0s",
            "Key": rating_to_key(row),
            **row,
        }
        for row in reader
    ]
    return sorted(ratings, key=itemgetter("Rating"))


def load_rankings(file, ratings=None):
    ratings = ratings or {}
    ratingsByKey = {
        rating_to_key(rating): rating
        for rating in ratings
    }
    reader = csv.DictReader(file)
    ratings = [
        {
            "Key": ranked_to_key(row),
            "Position": int(row["Position"]),
            "Description": row["Description"],
            **ratingsByKey.get(ranked_to_key(row)),
        }
        for row in reader
        if ranked_to_key(row) in ratingsByKey
    ]
    return sorted(ratings, key=itemgetter("Position"))


def load_diary(file):
    reader = csv.DictReader(file)
    dairy_entries = [
        {
            **row,
            "Key": line_to_key(row),
            "Tags": line_to_diary_tags(row),
        }
        for row in reader
    ]
    return dairy_entries


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


def rating_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    if name == "A Day in the Country":
        year = "1946"
    else:
        year = line["Year"]
    return f"{name} ({year})"


def ranked_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    year = line["Year"]
    return f"{name} ({year})"


def line_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    year = line["Year"]
    return f"{name} ({year})"


def line_to_diary_tags(line):
    tags = line.get("Tags")
    if tags:
        return tags.split(", ")
    return tags or None


def prompt_for_winner(a, b):
    response = None
    while response not in {"1", "2"}:
        prompt = dedent(
            f"""
            Which is best?
            1) {a}
            2) {b}
            """
        )
        response = input(prompt).upper()
    if response == '1':
        return a
    elif response == '2':
        return b
    else:
        print(f"Invalid response: {response}")
        return None


def prompt_for_loop(loop, delimiter="<<"):
    response = None
    while response not in range(1, len(loop)):
        if response == "":
            prompt = []
        else:
            prompt = ["Flip which segment?"]
            for i in range(0, len(loop)):
                movie = loop[i]
                if i:
                    prompt.append(f"    {delimiter}{i}{delimiter}")
                prompt.append(f"  {movie}")
        response = input("\n".join(prompt) + "\n")
        if response != "":
            try:
                    response = int(response)
            except ValueError:
                response = None
    return response


def prompt_for_segments(segments, movie_key=None):
    response = None
    while response not in range(0, len(segments)):
        if response == "":
            prompt = []
        else:
            prompt = ["Flip which segment?"]
            left = None
            right = None
            for i in range(0, len(segments)):
                segment = segments[i]
                left = segment["left"]
                if i != 0 and (left == movie_key or right == movie_key):
                    prompt.append("")
                right = segment["right"]
                count = segment["count"]
                if count > 1:
                    count = f"x{count}"
                else:
                    count = ""
                prompt.append(f"{i}:\t {count}\t {trunc_string(left)}\t <<<\t {trunc_string(right)}")
        response = input("\n".join(prompt) + "\n")
        if response != "":
            try:
                    response = int(response)
            except ValueError:
                response = None
    return response


def rating_sorter(a, b, verbose=True):
    a_key = rating_to_key(a)
    b_key = rating_to_key(b)
    if a_key == b_key:
        return 0
    memo_key = frozenset({a_key, b_key})
    if memo_key in memo:
        winner = memo[memo_key]
        if verbose:
            print(f"\tFound previous:\t {a_key}\t vs {b_key}\t => {winner}")
    else:
        winner = prompt_for_winner(a_key, b_key)
        memo[memo_key] = winner
    if a_key == winner:
        return 1
    elif b_key == winner:
        return -1
    else:
        return 0


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


def write_rankings(file, rankings):
    fieldnames = ["Position", "Name", "Year", "URL", "Description"]
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rankings)


def write_memo(file, comparisons):
    fieldnames = ["LeftKey", "RightKey", "Winner"]
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()
    rows = (
        {
            "LeftKey": sorted(list(key))[0],
            "RightKey": sorted(list(key))[1],
            "Winner": winner,
        }
        for key, winner in comparisons.items()
    )
    writer.writerows(sorted(rows, key=itemgetter("LeftKey", "RightKey")))


def clear_memo(comparisons, rating_key, secondary_key=None):
    keys_to_remove = [
        key
        for key in comparisons.keys()
        if rating_key in key
        if not secondary_key or secondary_key in key
    ]
    for key in keys_to_remove:
        previous = " vs. ".join(list(key))
        print(f"Cleared previous:\t {previous}")
        comparisons.pop(key, None)


def reverse_memo(comparisons, primary_key, secondary_key):
    key = frozenset([primary_key, secondary_key])
    winner = comparisons[key]
    if winner == primary_key:
        comparisons[key] = secondary_key
    elif winner == secondary_key:
        comparisons[key] = primary_key
    previous = " vs. ".join(list(key))
    print(f"Reversed\t {previous}\t to {comparisons[key]}")


def print_memo(comparisons, rating_key, rankingsByKey=None):
    rankingsByKey = rankingsByKey or {}
    higher_than = set()
    lower_than = set()
    for key in comparisons.keys():
        if rating_key in key:
            keys = list(key)
            a_key = keys[0]
            b_key = keys[1]
            if a_key == rating_key:
                them = b_key
            else:
                them = a_key
            winner = comparisons[key]
            if winner == rating_key:
                lower_than.add(them)
            else:
                higher_than.add(them)
    movie_label = build_movie_label(rankingsByKey.get(rating_key, rating_key))
    print(f"Movies lower than\t {movie_label}:")
    if rankingsByKey:
        lower_than = [
            build_movie_label(rankingsByKey.get(key, key)) 
            for key in lower_than
        ]
        higher_than = [
            build_movie_label(rankingsByKey.get(key, key)) 
            for key in higher_than
        ]
    for label in sorted(lower_than, reverse=True):
        print(f"\t {label}")
    print(f"Movies higher than\t {movie_label}:")
    for label in sorted(higher_than, reverse=True):
        print(f"\t {label}")


def add_memo(rankingsByKey, a_key, b_key):
    a_movie = rankingsByKey[a_key]
    b_movie = rankingsByKey[b_key]
    rating_sorter(a_movie, b_movie)


def build_thresholds(ratingIds, ratingCurve, totalRated):
    ratingThresholds = {}
    thresholdTotal = 0
    for rating in ratingIds:
        curve = ratingCurve[rating]
        thresholdTotal += totalRated * curve
        thresholdFloor = math.floor(thresholdTotal)
        if len(rating) == 1:
            rating = f"{rating}.0"
        percentage = math.floor(curve*100)
        ratingThresholds[thresholdFloor] = f"{rating} star threshold ({percentage: >2}%)"
    return ratingThresholds


def build_description(ratingThresholds):
    rankedDescription = [
        "From best to worst.",
        "",
    ]
    rankedDescription.extend([
        f"Rank {key: >3} is {value}"
        for key, value in ratingThresholds.items()
    ])
    return "\n".join(rankedDescription)


def build_movie_label(movie, position_prefix="#"):
    if isinstance(movie, str):
        return movie
    position = movie.get("Position")
    key = movie.get("Key")
    if position:
        position = str(position).rjust(4, ' ')
        return f"{position_prefix}{position} - {key}"
    return key


def sort_bubble_step(ratings, index):
    left = ratings[index]
    right = ratings[index+1]
    comp_result = rating_sorter(left, right, verbose=False)
    if comp_result == 1:
        print(f"Bubble swap: {rating_to_key(left)}\t now ahead of {rating_to_key(right)}")
        ratings[index] = right
        ratings[index+1] = left
        return True
    return False


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
    path = path or []
    path.append(curr_key)
    next_keys = comparisons.get(curr_key, [])
    for next_key in next_keys:
        if next_key == path[0]:
            loops.append([*path, next_key])
        else:
            loops.extend(find_comparison_loops(
                comparisons,
                next_key,
                path=[*path],
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


def fix_loop(memo, loop, delimiter="<<"):
    fix = prompt_for_loop(loop, delimiter)
    reverse_memo(memo, loop[fix-1], loop[fix])


def trunc_string(movie, length=35):
    if len(movie) > length:
        return movie[:length-3]+'...'
    return movie


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
        itemsRanked = sorted(items, key=cmp_to_key(rating_sorter))
        rankedByRating[rating] = itemsRanked
    # POST GROUP SORTING
    rankingWorstToBest = []
    for rating in starsWorstToBest:
        if rating in rankedByRating:
            rankingWorstToBest.extend(rankedByRating[rating])
    return rankingWorstToBest


def run_bubble_sorting(rankingWorstToBest):
    changes = True
    while changes:
        changes = 0
        for i in range(len(rankingWorstToBest) - 1):
            saw_change = sort_bubble_step(rankingWorstToBest, i)
            if saw_change:
                changes += 1
        print(f"Bubble finished with {changes} changes")


def run_search(rankingWorstToBest, movie):
    left = 0
    right = len(rankingWorstToBest) - 1
    while left <= right:
        curr = (left + right) // 2
        curr_movie = rankingWorstToBest[curr]
        comp_result = rating_sorter(movie, curr_movie)
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


def run_fix_multi_loop(movie_key, loops_higher_than, memo):
    hits = dict()
    pairs = list()
    for loop in loops_higher_than[-10:]:
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
    segments = sorted(segments, key=itemgetter("pos"))
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
                run_fix_multi_loop(movie_key, loops_higher_than, memo)
                run_bubble_sorting(rankingWorstToBest)
                break


# LOAD RATINGS
ratingsFile = f"{baseDir}/ratings.csv"
with open(ratingsFile, 'r') as file:
    ratingsUnsorted = load_ratings(file)

ratingsByKey = {
    rating_to_key(rating): rating
    for rating in ratingsUnsorted
}


# LOAD RANKINGS
rankingsFile = f"{baseDir}/rankings.csv"
with open(rankingsFile, 'r') as file:
    rankingsBestToWorst = load_rankings(file, ratingsUnsorted)

rankingWorstToBest = list(reversed(rankingsBestToWorst))
rankingsByKey = {
    ranked_to_key(movie): movie
    for movie in rankingsBestToWorst
}


# RUN GROUP SORTING
rankingWorstToBest = run_group_sorting(ratingsUnsorted)
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}


# INSERT MISSING RATINGS
run_missing_insert(ratingsUnsorted, rankingWorstToBest)


# RUN BUBBLE SORTING
run_bubble_sorting(rankingWorstToBest)


# PREP THRESHOLDS
rankingBestToWorst = list(reversed(rankingWorstToBest))
totalRated = len(rankingBestToWorst)
rankingThresholds = build_thresholds(reversed(starsWorstToBest), ratingCurve, totalRated)
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
rankingsFile = f"{baseDir}/rankings.csv"
with open(rankingsFile, 'w', newline='') as file:
    # write_metadata(file, rankedDescription)
    # file.write("\n")
    write_rankings(file, rankedOutput)


# SAVE MEMO
if memo:
    with open(memoFile, 'w', newline='') as file:
        write_memo(file, memo)


# FIX FIRST LOOP
run_fix_first_loop(
    memo,
    rankingBestToWorst,
    max_depth=3,
)


# DECADE GROUPING
ignoreStars = {
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
}
rankingsByDecade = sorted(rankingBestToWorst, key=itemgetter("Decade", "Position"))
count = 15
decadesBestToWorst = {
    k: {
        "decade": k,
        "movies": [
            movie
            for movie in g
            if movie["Rating"] not in ignoreStars
        ][:count],
    }
    for k, g in groupby(rankingsByDecade, key=itemgetter("Decade"))
}
for decade in decadesBestToWorst:
    movies = decadesBestToWorst[decade]["movies"]
    if len(movies) < count:
        continue
    print(decade)
    pprint([
        movie["Key"]
        for movie in movies
    ])

print(dedent(
    f"""
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


# LOAD DIARY
ignore_diary_keys = frozenset({
    "Anima (2019)",
    "Squid Game (2021)",
})
rankingsFile = f"{baseDir}/diary.csv"
with open(rankingsFile, 'r') as file:
    diary_entries = load_diary(file)

diary_by_key = {
    line_to_key(entry): entry
    for entry in diary_entries
}
diary_keys = frozenset(diary_by_key.keys())
ranking_keys = frozenset([
    line_to_key(movie)
    for movie in rankingWorstToBest
])
missing_keys = diary_keys - ranking_keys - ignore_diary_keys
output = []
for missing_key in missing_keys:
    missing_movie = diary_by_key[missing_key]
    position = run_search(rankingWorstToBest, missing_movie)
    position = len(rankingWorstToBest) - position
    for threshold in rankingThresholds:
        if threshold > position:
            threshold_label = rankingThresholds[threshold]
            print(f"AAA {threshold} vs {position} => {threshold_label}")
            break
    output.append(f"{missing_key} => {position} as {threshold_label}")

pprint(output)


# REINSERT
key_to_reinsert = "Coco (2017)"

rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}
ranking_to_reinsert = rankingsByKey[key_to_reinsert]
index = len(rankingWorstToBest) - ranking_to_reinsert["Position"]
if rankingWorstToBest[index]["Key"] == key_to_reinsert:
    del rankingWorstToBest[index]

clear_memo(memo, key_to_reinsert)
run_missing_insert(ratingsUnsorted, rankingWorstToBest)


# PRINT DELTAS
rankedDeltas = filter(lambda x: x["RatingDelta"], rankingBestToWorst)
for movie in rankedDeltas:
    if movie['RatingPrev'] < movie['RatingCurr']:
        delta = '▲'
    elif movie['RatingPrev'] > movie['RatingCurr']:
        delta = '▼'
    else:
        delta = ' '
    label = build_movie_label(movie, position_prefix=delta)
    print(f"{label}\t changed from {movie['RatingPrev']}\t to {movie['RatingCurr']}")


# UTILS
rankingsByKey = {
    ranked_to_key(ranking): ranking
    for ranking in rankingWorstToBest
}

clear_memo(memo, "Legend (1985)")
reverse_memo(memo, "Soul (2020)", "10 Cloverfield Lane (2016)")
print_memo(memo, "Soul (2020)", rankingsByKey)
print_memo(memo, "Ratatouille (2007)", rankingsByKey)

add_memo(rankingsByKey, "Candyman (1992)", "Candyman (2021)", verbose=True)

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

target_tag = "marathon-cube"
target_tag = "marathon-pixar"
target_tag_entires = sorted(
    [
        rankingsByKey.get(entry["Key"], entry)
        for entry in entries_by_tags[target_tag]
    ],
    key=cmp_to_key(rating_sorter),
    reverse=True,
)
print("\n" + "\n".join([
    build_movie_label(movie)
    for movie in target_tag_entires
]))

run_fix_first_loop(
    memo,
    target_tag_entires,
    max_depth=3,
)
