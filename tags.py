from itertools import groupby
from operator import itemgetter
from pprint import pprint
from labels import build_movie_label
from rankings import ranked_to_key
from ratings import rating_cmp


def rank_diary_by_subject(
    *,
    memo,
    ranking_worst_to_best,
    entries_by_subject,
    target_subject,
    use_position=False,
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
            key=rating_cmp(memo),
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