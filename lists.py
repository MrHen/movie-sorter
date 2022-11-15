import csv
import os
from operator import itemgetter

from prompt import trunc_string
from rankings import ranked_to_key

LISTS_DIR = 'lists'


def multisort(xs, specs):
    for key, reverse in reversed(specs):
        xs.sort(key=itemgetter(key), reverse=reverse)
    return xs


def load_list_names(*, list_dir=LISTS_DIR):
    list_names = []
    with os.scandir(list_dir) as scanner:
        for entry in scanner:
            if not entry.name.startswith('.') and entry.is_file():
                list_names.append(entry.name)
    return list_names


def load_list(*, list_dir=LISTS_DIR, list_name):
    with open(f"{list_dir}/{list_name}", newline="", encoding='UTF-8') as list_file:
        reader = csv.reader(list_file)
        blank = next(reader)
        metadata_header = next(reader)
        metadata = next(reader)
        blank = next(reader)
        header = next(reader)
        movies = list(dict(zip(header, movie)) for movie in reader)
    return {
        "name": list_name[:-4],
        "metadata": dict(zip(metadata_header, metadata)),
        "movies": movies,
    }


def merge_lists(*, lists):
    weights = {}
    full = {}
    for list in lists:
        movies = list["movies"]
        count = len(movies)
        for movie in movies:
            url = movie["URL"]
            if url not in full:
                full[url] = movie
            if "Matches" not in full[url]:
                full[url]["Matches"] = []
            full[url]["Matches"].append(list["metadata"]["Name"])
            weights[url] = weights.get(url, 0) + (1 / count)
    return [
        {
            **movie,
            "Description": "\n".join([*movie["Matches"], "", f"{weights[url]}"]),
            "Weight": weights[url],
        }
        for url, movie in full.items()
    ]


def write_stats_combo(*, movies, filename):
    fieldnames = ["Position", "Name", "Year", "URL", "Description"]
    with open(filename, 'w', newline='', encoding='UTF-8') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(movies)


def write_file_parts(*, movies, filename, batch_size=1000):
    for i in range(0, len(movies), batch_size):
        write_stats_combo(movies=movies[i:i+batch_size], filename=f"{filename}_{i:04}.csv")


def create_weighted_list(*, list_data, tag):
    stats_combo = [
        list_datum
        for list_datum in list_data
        if tag in list_datum["metadata"]["Tags"].split(", ")
    ]
    merged = merge_lists(lists=stats_combo)
    merged = multisort(
        list(merged),
        (
            ('Weight', True),
            ('Year', False),
            ('Name', False),
        ),
    )
    merged = [
        {
            **merged[i],
            "Position": i + 1,

        }
        for i in range(0, len(merged))
    ]
    return merged


def print_list_comparison(a, b):
    b_keys = [
        ranked_to_key(movie)
        for movie in b
    ]
    a_keys = [
        ranked_to_key(movie)
        for movie in a
    ]
    max_len = max(len(a_keys), len(b_keys))
    for i in range(0, max_len):
        index = i+1
        if i < len(a):
            a_key = a_keys[i]
        else:
            a_key = '-'
        if i < len(b):
            b_key = b_keys[i]
        else:
            b_key = '-'
        match = a_key == b_key
        print(f"#{index}\t {match}\t {trunc_string(a_key)}\t {trunc_string(b_key)}")


def do_lists_match(a, b):
    b_keys = [
        ranked_to_key(movie)
        for movie in b
    ]
    a_keys = [
        ranked_to_key(movie)
        for movie in a
    ]
    return b_keys == a_keys
