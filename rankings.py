import csv

from operator import itemgetter

from ratings import rating_to_key

def ranked_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    year = line["Year"]
    return f"{name} ({year})"


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


def load_rankings_basic(file):
    reader = csv.DictReader(file)
    ratings = [
        {
            **row,
            "Key": ranked_to_key(row),
            "Position": int(row["Position"]),
        }
        for row in reader
    ]
    return ratings


def write_rankings(file, rankings):
    fieldnames = ["Position", "Name", "Year", "LetterboxdURI", "Description"]
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rankings)
