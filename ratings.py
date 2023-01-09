import csv

from functools import cmp_to_key
from operator import itemgetter
from labels import build_movie_label

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


def rating_sorter(
    a,
    b,
    memo,
    *,
    verbose=True,
    reverse=False,
    use_label=False,
    changes=None,
):
    detail = rating_sorter_detail(a, b, memo, verbose=verbose, reverse=reverse, use_label=use_label)
    if changes is not None and detail["change"]:
        changes.append(detail["change"])
    return detail["result"]


def rating_sorter_detail(
        a,
        b,
        memo,
        verbose=True,
        reverse=False,
        use_label=False,
):
    detail = {
        "change": None,
    }
    a_key = rating_to_key(a)
    b_key = rating_to_key(b)
    if use_label:
        a_label = build_movie_label(a)
        b_label = build_movie_label(b)
    else:
        a_label = a_key
        b_label = b_key
    if a_key == b_key:
        detail["result"] = 0
        return detail
    memo_key = frozenset({a_key, b_key})
    if memo_key in memo:
        winner_key = memo[memo_key]
        if verbose:
            print(f"\tFound previous:\t {a_label}\t vs {b_label}\t => {winner_key}")
    else:
        winner_label = prompt_for_winner(a_label, b_label)
        if winner_label == a_label:
            winner_key = a_key
            loser_key = b_key
        else:
            winner_key = b_key
            loser_key = a_key
        memo[memo_key] = winner_key
        detail["change"] = {
            "winner": winner_key,
            "loser": loser_key,
        }
    if a_key == winner_key:
        detail["result"] = -1 if reverse else 1
    elif b_key == winner_key:
        detail["result"] = 1 if reverse else -1
    else:
        detail["result"] = 0
    return detail


def rating_cmp(memo, verbose=True, use_label=False, changes=None):
    return cmp_to_key(lambda a, b: rating_sorter(
        a,
        b,
        memo,
        verbose=verbose,
        use_label=use_label,
        changes=changes,
    ))
