from textwrap import dedent


def prompt_for_winner(a, b):
    response = None
    while response not in {"1", "2"}:
        prompt = dedent(
            f"""
            Which is best?
            1) {a}
            2) {b}
            """
        )
        response = input(prompt).upper()
    if response == '1':
        return a
    elif response == '2':
        return b
    else:
        print(f"Invalid response: {response}")
        return None


def prompt_for_loop(loop, delimiter="<<"):
    response = None
    while response not in range(1, len(loop)):
        if response == "":
            prompt = []
        else:
            prompt = ["Flip which segment?"]
            for i in range(0, len(loop)):
                movie = loop[i]
                if i:
                    prompt.append(f"    {delimiter}{i}{delimiter}")
                prompt.append(f"  {movie}")
        response = input("\n".join(prompt) + "\n")
        if response != "":
            try:
                    response = int(response)
            except ValueError:
                response = None
    return response


def prompt_for_segments(segments, movie_key=None):
    response = None
    while response not in range(0, len(segments)):
        if response == "":
            prompt = []
        else:
            prompt = ["Flip which segment?"]
            left = None
            right = None
            for i in range(0, len(segments)):
                segment = segments[i]
                left = segment["left"]
                if i != 0 and (left == movie_key or right == movie_key):
                    prompt.append("")
                right = segment["right"]
                count = segment["count"]
                if count > 1:
                    count = f"x{count}"
                else:
                    count = ""
                prompt.append(f"{i}:\t {count}\t {trunc_string(left)}\t <<<\t {trunc_string(right)}")
        response = input("\n".join(prompt) + "\n")
        if response != "":
            try:
                    response = int(response)
            except ValueError:
                response = None
    return response


def trunc_string(movie, length=35):
    if len(movie) > length:
        return movie[:length-3]+'...'
    return movie
