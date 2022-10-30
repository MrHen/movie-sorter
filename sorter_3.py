from pprint import pprint
from operator import itemgetter
from bubble import bubble_pass
from dairy import line_to_key
from files import load_diary_file, load_memo_file, load_rankings_file, load_ratings_file, reload_all, run_search, write_memo_file, write_rankings_file
from graph import memo_to_graph
from loops import run_fix_multi_loop
from loops_graph import graph_to_loops
from memo import set_memo
from rankings import ranked_to_key
from ratings import rating_to_key
from thresholds import build_description, build_thresholds


memo = {}
diary_entries = []
ratings_unsorted = []
rankings_worst_to_best = []
movies_by_key = {}

stars_worst_to_best = [
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
    "4",
    "4.5",
    "5",
]
# https://www.wolframalpha.com/input/?i=-0.08+x%5E3+%2B+0.7+x%5E2+%2B+1.3+x+%2B+0.1+for+x+between+1+and+10
rating_curve = {
    "0.5": 0.02,
    "1": 0.05,
    "1.5": 0.08,
    "2": 0.11,
    "2.5": 0.14,
    "3": 0.16,
    "3.5": 0.16,
    "4": 0.14,
    "4.5": 0.1,
    "5": 0.04,
}
sum(rating_curve.values())


def reset():
    global memo
    memo = load_memo_file()


def reload():
    global diary_entries
    global ratings_unsorted
    global rankings_worst_to_best
    global movies_by_key
    diary_entries = load_diary_file()
    ratings_unsorted = load_ratings_file()
    rankings_unsorted = load_rankings_file()
    ratings_by_key = {
        rating_to_key(rating): rating
        for rating in ratings_unsorted
    }
    rankings_by_key = {
        ranked_to_key(ranking): ranking
        for ranking in rankings_unsorted
    }
    diary_by_key = {
        line_to_key(entry): entry
        for entry in diary_entries
        if not movie_has_diary_tag(entry, 'ignore-ranking')
    }
    rating_keys = frozenset(ratings_by_key.keys())
    ranking_keys = frozenset(rankings_by_key.keys())
    diary_keys = frozenset(diary_by_key.keys())
    movie_keys = rating_keys | ranking_keys | diary_keys
    movies_by_key = {
        movie_key: {
            **ratings_by_key.get(movie_key, {}),
            **{
                key: diary_by_key.get(movie_key, {}).get(key, None)
                for key in diary_by_key.get(movie_key, {}).keys()
                if key in {'Watched Date', 'Watched Month', 'Tags'}
            },
            **{
                key: rankings_by_key.get(movie_key, {}).get(key, None)
                for key in rankings_by_key.get(movie_key, {}).keys()
                if key in {'Position'}
            },
            "Key": movie_key,
        }
        for movie_key in movie_keys
    }
    rankings_worst_to_best = sorted([
        movie
        for movie in movies_by_key.values()
        if movie_has_ranking(movie)
    ], key=itemgetter("Position"), reverse=True)


def movie_has_ranking(movie):
    return movie.get('Position', None) is not None


def movie_has_rating(movie):
    return movie.get('Rating', None) is not None


def movie_has_diary(movie):
    return movie.get('Watched Date', None) is not None


def movie_has_diary_tag(movie, tag):
    return tag in (movie.get('Tags', None) or [])


# SAVE
def rerank(
    *,
    rankings_worst_to_best,
    stars_worst_to_best,
    rating_curve,
):
    total_rated = len(rankings_worst_to_best)
    ranking_thresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, total_rated)
    ranking_description = build_description(ranking_thresholds)
    print(ranking_description)
    rating_curr = 5
    for i in range(0, len(rankings_worst_to_best)):
        movie = rankings_worst_to_best[total_rated - i - 1]
        position = i + 1
        description = ranking_thresholds.get(position, None)
        movie["Position"] = position
        movie["Description"] = description
        movie["RatingCurr"] = str(rating_curr)
        movie["RatingPrev"] = movie["Rating"]
        movie["RatingDelta"] = rating_curr - float(movie["Rating"])
        if description:
            rating_curr -= 0.5


def save_all(
    *,
    memo=memo,
    rankings_worst_to_best,
):
    rankings_best_to_worst = list(reversed(rankings_worst_to_best))
    rankings_output = [
        {
            "Position": movie["Position"],
            "Name": movie["Name"],
            "Year": movie["Year"],
            "URL": movie["Letterboxd URI"],
            "Description": movie["Description"],
        }
        for movie in rankings_best_to_worst
    ]
    write_rankings_file(rankings_output)
    write_memo_file(memo)


# UPDATE RANKINGS
def update_rankings(
    *,
    memo,
    movies_by_key,
    rankings_worst_to_best,
):
    missing_keys = {
        movie_key
        for movie_key, movie in movies_by_key.items()
        if movie_has_rating(movie) and not movie_has_ranking(movie)
    }
    for missing_key in missing_keys:
        missing_movie = movies_by_key[missing_key]
        missing_index = run_search(memo, rankings_worst_to_best, missing_movie)
        rankings_worst_to_best.insert(missing_index, missing_movie)


# RATE DIARY ENTRIES
def update_diary(
    *,
    memo,
    movies_by_key,
    stars_worst_to_best,
    rating_curve,
    rankings_worst_to_best,
):
    total_rated = len(rankings_worst_to_best)
    ranking_thresholds = build_thresholds(reversed(stars_worst_to_best), rating_curve, total_rated)
    missing_keys = {
        movie_key
        for movie_key, movie in movies_by_key.items()
        if movie_has_diary(movie)
        if not movie_has_ranking(movie)
        if not movie_has_diary_tag(movie, 'ignore-ranking')
    }
    output = []
    for missing_key in missing_keys:
        missing_movie = movies_by_key[missing_key]
        position = run_search(memo, rankings_worst_to_best, missing_movie)
        position = len(rankings_worst_to_best) - position
        for threshold in ranking_thresholds:
            if threshold > position:
                threshold_label = ranking_thresholds[threshold]
                break
        output.append(f"{missing_key} => {position} as {threshold_label}")
    return output


# FIX SHORT CYCLES
def fix_adjacent(
    *,
    memo,
    rankings_worst_to_best,
    verbose=False,
):
    changes_memo = bubble_pass(
        memo,
        rankings_worst_to_best,
        # step=1,
        # do_swap=False,
        # max_changes=1,
        max_changes_memo=None,
        reverse=True,
        verbose=verbose,
        use_label=True,
    )
    return changes_memo


def fix_small_loop(
    *,
    memo,
    ranking_worst_to_best,
    verbose=True,
    max_segments=20,
):
    changes = []
    graph = memo_to_graph(memo)
    ranking_best_to_worst = list(reversed(ranking_worst_to_best))
    loops = graph_to_loops(
        graph=graph,
        rankings=ranking_best_to_worst,
        cutoff=2,
        max_loops=1,
        verbose=verbose,
    )
    if loops:
        print(f"\n{len(loops)} segments\n")
        fix = run_fix_multi_loop(
            loops,
            # movie_key=ranking_key,
            max_segments=max_segments,
            # sort_key=sort_key,
            # sort_reversed=sort_reversed,
        )
        if fix:
            change = {
                "loser": fix["right"],
                "winner": fix["left"],
            }
            changes.append(change)
            set_memo(memo, change["loser"], change["winner"], verbose=verbose)
    return changes


def clean_up_gen(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
):
    print(f'\t... running fix_adjacent')
    changes = fix_adjacent(
        memo=memo,
        rankings_worst_to_best=rankings_worst_to_best,
    )
    if not changes:
        print(f'\t... running fix_small_loop')
        changes = fix_small_loop(
            memo=memo,
            ranking_worst_to_best=rankings_worst_to_best,
        )
    changes = changes or []
    return (change for change in changes)


def clean_up(
    *,
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
):
    total_changes = []
    saw_change = True
    while saw_change:
        print('Starting clean up...')
        saw_change = False
        changes = clean_up_gen(
            memo=memo,
            rankings_worst_to_best=rankings_worst_to_best,
        )
        for change in changes:
            print(f'\t... saw change {change["winner"]} >>> {change["loser"]}')
            total_changes.append(change)
            saw_change = True


# FIX TOPICAL CYCLES

# FIX EVERYTHING


### ONCE PER RUN

reset()


### ONCE PER DIARY CYCLE

reload()

update_rankings(
    memo=memo,
    movies_by_key=movies_by_key,
    rankings_worst_to_best=rankings_worst_to_best,
)
pprint(sorted(update_diary(
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
    rating_curve=rating_curve,
    stars_worst_to_best=stars_worst_to_best,
    movies_by_key=movies_by_key,
)))

rerank(
    rankings_worst_to_best=rankings_worst_to_best,
    stars_worst_to_best=stars_worst_to_best,
    rating_curve=rating_curve,
)
save_all(
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
)

### CLEAN UP

clean_up(
    memo=memo,
    rankings_worst_to_best=rankings_worst_to_best,
)
