def build_movie_label(movie, position_prefix="#"):
    if isinstance(movie, str):
        return movie
    position = movie.get("Position")
    key = movie.get("Key")
    if position:
        position = str(position).rjust(4, ' ')
        return f"{position_prefix}{position} - {key}"
    return key
