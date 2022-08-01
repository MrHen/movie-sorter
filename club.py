import csv
from pprint import pprint

voting_file = "voting/Season 5 Week 7 Voting.csv"
with open(voting_file, newline="", encoding='UTF-8') as file:
    reader = csv.DictReader(file)
    votes = [
        row
        for row in reader
    ]

keys = [
    "First Pick",
    "Second Pick",
    "Third Pick",
    "Fourth Pick",
    "Fifth Pick",
]

all_movies = set()
for vote in votes:
    movies = [
        vote[key]
        for key in keys
    ]
    for movie in movies:
        all_movies.add(movie.split(" (")[0])
    print("\n")
    print("\n".join(movies))

print("\n")
print("\n".join(all_movies))
