import csv

def line_to_key(line):
    if "Key" in line:
        return line.get("Key")
    name = line["Name"]
    year = line["Year"]
    return f"{name} ({year})"


def line_to_diary_tags(line):
    tags = line.get("Tags")
    if tags:
        return tags.split(", ")
    return tags or None


def load_diary(file):
    reader = csv.DictReader(file)
    dairy_entries = [
        {
            **row,
            "Watched Month": row.get("Watched Date", "")[:7] or None,
            "Key": line_to_key(row),
            "Tags": line_to_diary_tags(row),
        }
        for row in reader
    ]
    return dairy_entries
