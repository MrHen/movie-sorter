
from dairy import line_to_key, load_diary
from memo import write_memo
from rankings import load_rankings, write_rankings
from ratings import load_ratings, rating_sorter
from thresholds import build_description, build_thresholds


def run_search(memo, ranking_worst_to_best, movie, use_label=False):
    left = 0
    right = len(ranking_worst_to_best) - 1
    while left <= right:
        curr = (left + right) // 2
        curr_movie = ranking_worst_to_best[curr]
        comp_result = rating_sorter(movie, curr_movie, memo, use_label=use_label)
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
    ratings_file = f"{base_dir}/ratings.csv"
    with open(ratings_file, 'r') as file:
        ratings_unsorted = load_ratings(file)
    # LOAD RANKINGS
    rankings_file = f"{base_dir}/rankings.csv"
    with open(rankings_file, 'r') as file:
        rankings_best_to_worst = load_rankings(file, ratings_unsorted)
    rankings_worst_to_best = list(reversed(rankings_best_to_worst))
    # LOAD DIARY
    rankings_file = f"{base_dir}/diary.csv"
    with open(rankings_file, 'r') as file:
        diary_entries = load_diary(file)
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
        if "ignore-ranking" not in (entry["Tags"] or [])
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
        with open(memo_file, 'w', newline='') as file:
            write_memo(file, memo)

