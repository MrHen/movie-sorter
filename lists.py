import csv
import os
from operator import itemgetter

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
    with open(f"{list_dir}/{list_name}", newline="") as list_file:
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
    with open(filename, 'w', newline='') as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(movies)


list_names = load_list_names()
list_data = [
    load_list(list_name=list_name)
    for list_name in list_names
]
stats_combo = [
    list_datum
    for list_datum in list_data
    if list_datum["metadata"]["Tags"] == "stats-tracker"
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
write_stats_combo(movies=merged[:1000], filename="stats_combo_a.csv")
write_stats_combo(movies=merged[1000:2000], filename="stats_combo_b.csv")
write_stats_combo(movies=merged[2000:], filename="stats_combo_c.csv")
