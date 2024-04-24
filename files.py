import csv
import json
import math

import constants
from dairy import line_to_key, load_diary
from memo import load_memo, write_memo
from rankings import load_rankings, load_rankings_basic, write_rankings
from ratings import load_ratings, rating_sorter
from thresholds import build_description, build_thresholds


def load_diary_file(*, base_dir=constants.BASE_DIR):
    # Movies logged that no longer exist on Letterboxd
    ignore_diary_keys = frozenset({
        "Family Dog (1987)",
        "Not so fast (2019)",
        "Astartes (2020)",
    })
    rankings_file = f"{base_dir}/diary.csv"
    with open(rankings_file, 'r', encoding='UTF-8') as file:
        diary_entries = load_diary(file)
    return [
        entry
        for entry in diary_entries
        if line_to_key(entry) not in ignore_diary_keys
    ]


def load_ratings_file(*, base_dir=constants.BASE_DIR):
    ratings_file = f"{base_dir}/ratings.csv"
    with open(ratings_file, 'r', encoding='UTF-8') as file:
        ratings_unsorted = load_ratings(file)
    return ratings_unsorted


def load_memo_file(*, filename='memo.csv', base_dir=constants.BASE_DIR):
    memo_file = f"{base_dir}/{filename}"
    with open(memo_file, 'r', encoding='UTF-8') as file:
        memo_data = load_memo(file)
    return memo_data


def write_memo_file(memo_output, *, base_dir=constants.BASE_DIR):
    memo_file = f"{base_dir}/memo.csv"
    with open(memo_file, 'w', newline='', encoding='UTF-8') as file:
        write_memo(file, memo_output)


def load_rankings_file(*, base_dir=constants.BASE_DIR):
    rankings_file = f"{base_dir}/rankings.csv"
    with open(rankings_file, 'r', encoding='UTF-8') as file:
        rankings_unsorted = load_rankings_basic(file)
    return rankings_unsorted


def write_rankings_file(rankings_output, *, base_dir=constants.BASE_DIR):
    rankingsFile = f"{base_dir}/rankings.csv"
    with open(rankingsFile, 'w', newline='', encoding='UTF-8') as file:
        write_rankings(file, rankings_output)


def run_search(
    memo,
    ranking_worst_to_best,
    movie,
    reverse=False,
    use_label=False,
    *,
    verbose=True
):
    left = 0
    right = len(ranking_worst_to_best) - 1
    while left <= right:
        curr = (left + right) // 2
        curr_movie = ranking_worst_to_best[curr]
        comp_result = rating_sorter(movie, curr_movie, memo, reverse=reverse, use_label=use_label)
        if verbose:
            print(f"Searching... {left}|{curr}|{right} -> {comp_result}")
        if comp_result == 1:
            left = curr + 1
        elif comp_result == -1:
            right = curr - 1
        else:
            return curr
    return curr


def reload_all(*, base_dir):
    # LOAD RATINGS
    ratings_unsorted = load_ratings_file(base_dir=base_dir)
    # LOAD RANKINGS
    rankings_file = f"{base_dir}/rankings.csv"
    with open(rankings_file, 'r', encoding='UTF-8') as file:
        rankings_best_to_worst = load_rankings(file, ratings_unsorted)
    rankings_worst_to_best = list(reversed(rankings_best_to_worst))
    # LOAD DIARY
    diary_entries = load_diary_file(base_dir=base_dir)
    return {
        "ratings": ratings_unsorted,
        "rankings": rankings_worst_to_best,
        "diary_entries": diary_entries,
    }


def reload_diary(
    *,
    memo,
    stars_worst_to_best,
    rating_curve,
    ranking_worst_to_best,
    diary_entries,
):
    # PREP THRESHOLDS
    ranking_best_to_worst = list(reversed(ranking_worst_to_best))
    total_rated = len(ranking_best_to_worst)
    ranking_thresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, total_rated)
    # LOAD DIARY
    ignore_diary_keys = frozenset({
        "Family Dog (1987)",
    })
    diary_by_key = {
        line_to_key(entry): entry
        for entry in diary_entries
        if ("ignore-ranking" not in (entry["Tags"] or [])) and ("read-screenplay" not in (entry["Tags"] or []))
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
        position = run_search(memo, ranking_worst_to_best, missing_movie)
        position = len(ranking_worst_to_best) - position
        for threshold in ranking_thresholds:
            if threshold > position:
                threshold_label = ranking_thresholds[threshold]
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
    memo_file,
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
            "LetterboxdURI": movie["Letterboxd URI"],
            "Description": movie["Description"],
        }
        for movie in rankingBestToWorst
    ]
    rankingsFile = f"{base_dir}/rankings.csv"
    with open(rankingsFile, 'w', newline='', encoding='UTF-8') as file:
        # write_metadata(file, rankedDescription)
        # file.write("\n")
        write_rankings(file, rankedOutput)
    # SAVE MEMO
    if memo:
        with open(memo_file, 'w', newline='', encoding='UTF-8') as file:
            write_memo(file, memo)


def save_hierarchy(
    *,
    base_dir=constants.BASE_DIR,
    graph,
    ranking_worst_to_best,
):
    edgeData = [
        {
            "name": ranking["Key"],
            "successors": list(graph.successors(ranking["Key"])),
            "position": ranking["Position"],
            "path": "|".join([
                f"all",
                str(math.floor(math.log2(ranking['Position']))).zfill(4),
                str(ranking['Position']).zfill(4),
                ranking["Key"],
            ]),
        }
        for ranking in ranking_worst_to_best
        if graph.has_node(ranking["Key"])
    ]
    edgesFile = f"{base_dir}/hierarchy.json"
    with open(edgesFile, 'w', newline='', encoding='UTF-8') as file:
        file.write(json.dumps(edgeData, indent=2))


def save_arc_data(
    *,
    base_dir,
    graph,
    ranking_worst_to_best,
):
    nodes = list()
    links = list()
    for ranking in ranking_worst_to_best:
        if not graph.has_node(ranking["Key"]):
            continue
        nodes.append({
            "id": ranking["Key"],
            "group": ranking["Rating"],
            "year": ranking["Year"],
            "decade": ranking["Decade"],
            "position": ranking["Position"],
        })
        links.extend([
            {
                "source": ranking["Key"],
                "target": successor,
                "value": 1,
            }
            for successor in graph.successors(ranking["Key"])
        ])
    arcData = {
        "nodes": nodes,
        "links": links,
    }
    arcDataFile = f"{base_dir}/arc_data.json"
    with open(arcDataFile, 'w', newline='', encoding='UTF-8') as file:
        file.write(json.dumps(arcData, indent=2))
