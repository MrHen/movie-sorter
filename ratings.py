import csv

from functools import cmp_to_key
from operator import itemgetter

from prompt import prompt_for_winner


def rating_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    if name == "A Day in the Country":
        year = "1946"
    else:
        year = line["Year"]
    return f"{name} ({year})"


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


def rating_sorter(a, b, memo, verbose=True):
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


def rating_cmp(memo, verbose=True):
    return cmp_to_key(lambda a, b: rating_sorter(a, b, memo, verbose=verbose))
