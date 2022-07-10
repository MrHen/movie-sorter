from itertools import groupby
from operator import itemgetter
from pprint import pprint
from labels import build_movie_label
from loops import run_fix_all_loops
from rankings import ranked_to_key
from ratings import rating_cmp


def rank_diary_by_subject(
    *,
    memo,
    ranking_worst_to_best,
    entries_by_subject,
    target_subject,
    use_position=False,
    verbose=False,
):
    key_index = "Key"
    rankingsByKey = {
        ranked_to_key(ranking): ranking
        for ranking in ranking_worst_to_best
    }
    target_entries = [
        rankingsByKey.get(entry[key_index], entry)
        for entry in entries_by_subject[target_subject]
    ]
    if use_position:
        target_entries = sorted(
            target_entries,
            key=itemgetter("Position"),
        )
    else:
        target_entries = sorted(
            target_entries,
            key=rating_cmp(memo, verbose=verbose),
            reverse=True,
        )
    return target_entries


def group_diary_by_tag(
    *,
    diary_entries,
):
    key_index = "Key"
    tag_index = "Tag"
    tags_index = "Tags"
    entries_by_tags = {
        k: sorted(g, key=itemgetter(key_index))
        for k, g in groupby(
            sorted(
                [
                    {
                        key_index: entry.get(key_index),
                        tag_index: tag,
                    }
                    for entry in diary_entries
                    if entry.get(tags_index)
                    for tag in entry.get(tags_index)
                ],
                key=itemgetter(tag_index)
            ),
            key=itemgetter(tag_index),
        )
    }
    return entries_by_tags


def group_diaries_by_month(
    *,
    diary_entries,
):
    key_index = "Key"
    watched_month_index = "Watched Month"
    entries_by_month = {
        k: sorted(g, key=itemgetter(key_index))
        for k, g in groupby(
            sorted(
                [
                    entry
                    for entry in diary_entries
                    if entry.get(watched_month_index)
                    if "ignore-ranking" not in (entry.get("Tags") or [])
                ],
                key=itemgetter(watched_month_index)
            ),
            key=itemgetter(watched_month_index),
        )
    }
    return entries_by_month


def group_rankings_by_decade(
    *,
    ranking_worst_to_best,
):
    ignoreStars = {
        "0.5",
        "1",
        "1.5",
        "2",
        "2.5",
        "3",
        "3.5",
    }
    rankingBestToWorst = list(reversed(ranking_worst_to_best))
    rankingsWithoutIgnored = filter(lambda movie: movie["Rating"] not in ignoreStars, rankingBestToWorst)
    rankingsByDecade = sorted(rankingsWithoutIgnored, key=itemgetter("Decade", "Position"))
    decadesBestToWorst = {
        k: sorted(g, key=itemgetter("Key"))
        for k, g in groupby(rankingsByDecade, key=itemgetter("Decade"))
    }
    return decadesBestToWorst


def run_rank_by_subject(
    *,
    memo,
    ranking_worst_to_best,
    entries_by_subject,
    subjects,
):
    for target_subject in subjects:
        saw_changes = True
        print(f"Starting ranking for {target_subject}")
        while saw_changes:
            saw_changes = False
            print(f"...rank entries for {target_subject}")
            before = len(memo.keys())
            rank_diary_by_subject(
                memo=memo,
                ranking_worst_to_best=ranking_worst_to_best,
                entries_by_subject=entries_by_subject,
                target_subject=target_subject,
            )
            after = len(memo.keys())
            if after > before:
                print(f"...fix loops for {target_subject}")
                saw_changes = run_fix_all_loops(
                    ranking_worst_to_best=ranking_worst_to_best,
                    memo=memo,
                    max_depth=3,
                    max_segments=20,
                    max_loops=100,
                    # max_loops=None,
                    # sort_key="count",
                    # sort_reversed=True,
                )
        print(f"...finished {target_subject}\n")
