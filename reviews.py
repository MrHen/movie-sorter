import csv

def line_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    year = line["Year"]
    return f"{name} ({year})"


def line_to_tags(line):
    tags = line.get("Tags")
    if tags:
        return tags.split(", ")
    return tags or None


def load_reviews(file):
    reader = csv.DictReader(file)
    entries = [
        {
            **row,
            "Key": line_to_key(row),
            "Tags": line_to_tags(row),
        }
        for row in reader
    ]
    return entries

## Generate Word Cloud
import constants
import pprint

base_dir = constants.BASE_DIR
review_file = f"{base_dir}/reviews.csv"
with open(review_file, 'r', encoding='UTF-8') as file:
    reviews = load_reviews(file)

wordcloud_file = f"{base_dir}/reviews_wordcloud.csv"
with open(wordcloud_file, 'w', encoding='UTF-8', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['Review'], extrasaction='ignore')
    writer.writeheader()
    for review in reviews:
        writer.writerow({'Review': review['Review'].replace('\n', ' ')})
