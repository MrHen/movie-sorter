import csv

from operator import itemgetter

from labels import build_movie_label, normalize_key
from ratings import rating_sorter


def load_memo(file):
    # LeftKey,RightKey,Winner
    reader = csv.DictReader(file)
    comparisons = {
        frozenset({
            normalize_key(row["LeftKey"]),
            normalize_key(row["RightKey"])
        }): (normalize_key(row["Winner"]) or None)
        for row in reader
    }
    return comparisons


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


def set_memo(memo, loser, winner, verbose=False):
    key = frozenset([loser, winner])
    if verbose:
        if key in memo and memo[key] != winner:
            print(f'\t... updating {key} to {winner}')
    memo[key] = winner


def analyze_memo(comparisons, rating_key, rankingsByKey=None):
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
    return {
        "higher_than": [rankingsByKey.get(key, key) for key in higher_than],
        "lower_than": [rankingsByKey.get(key, key) for key in lower_than],
    }


def print_memo(comparisons, rating_key, rankingsByKey=None):
    rankingsByKey = rankingsByKey or {}
    results = analyze_memo(comparisons, rating_key, rankingsByKey=rankingsByKey)
    higher_than = results["higher_than"]
    lower_than = results["lower_than"]
    lower_than = [
        build_movie_label(movie) 
        for movie in lower_than
    ]
    higher_than = [
        build_movie_label(movie) 
        for movie in higher_than
    ]
    movie_label = build_movie_label(rankingsByKey.get(rating_key, rating_key))
    print(f"Movies lower than\t {movie_label}:")
    for label in sorted(lower_than, reverse=True):
        print(f"\t {label}")
    print(f"Movies higher than\t {movie_label}:")
    for label in sorted(higher_than, reverse=True):
        print(f"\t {label}")


def add_memo(rankingsByKey, a_key, b_key):
    a_movie = rankingsByKey[a_key]
    b_movie = rankingsByKey[b_key]
    rating_sorter(a_movie, b_movie)
