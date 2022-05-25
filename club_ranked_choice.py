import csv
from pprint import pprint
from itertools import groupby
from operator import itemgetter
import re

pick_order = [
    "First Pick",
    "Second Pick",
    "Third Pick",
    "Fourth Pick",
    "Fifth Pick",
]

voting_file = "voting/Season 5 Week 6 Voting.csv"
with open(voting_file, newline="") as file:
    reader = csv.DictReader(file)
    votes = [
        row
        for row in reader
    ]

pivoted = [
    {
        "movie": re.sub(r"[^A-Za-z]", "", vote_key),
        "vote": vote_value,
        "vote_order": pick_order.index(vote_value),
        "voter": re.sub(r"[^A-Za-z]", "", vote["Discord Name"]),
    }
    for vote in votes
    for vote_key, vote_value in vote.items()
    if vote_value not in ['']
    if vote_key not in ['Timestamp', 'Discord Name']
]

votes_sorted = sorted(pivoted, key=itemgetter("voter", "vote_order"))
votes_grouped = groupby(votes_sorted, key=itemgetter("voter"))

ranked_input = [
    "".join([
        # k,
        # ":",
        ">".join([
            vote["movie"]
            for vote in g
        ]),
    ])
    for k, g in votes_grouped
]

print("\n")
print("\n".join(ranked_input))
