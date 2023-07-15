import re

def build_movie_label(movie, position_prefix="#"):
    if isinstance(movie, str):
        return movie
    position = movie.get("Position")
    key = movie.get("Key")
    if position:
        position = str(position).rjust(4, ' ')
        return f"{position_prefix}{position} - {key}"
    return key


def normalize_key(key):
    if key is None:
        return None
    normalized = re.sub(r'\s+', ' ', key)
    normalized = re.sub(r'[-–]', '-', key)
    return normalized
