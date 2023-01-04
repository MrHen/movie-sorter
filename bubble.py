from ratings import rating_sorter, rating_sorter_detail, rating_to_key


def sort_bubble_step(
    memo,
    ratings,
    index,
    verbose=False,
    step=1,
    do_swap=True,
    reverse=False,
    use_label=False,
):
    left = ratings[index]
    right = ratings[index+step]
    detail = rating_sorter_detail(
        left,
        right,
        memo,
        verbose=verbose,
        reverse=reverse,
        use_label=use_label,
    )
    can_swap = detail["result"] == 1
    if do_swap and can_swap:
        verb = "behind" if reverse else "ahead of"
        print(f"Bubble swap: {rating_to_key(left)}\t now {verb} {rating_to_key(right)}")
        ratings[index] = right
        ratings[index+step] = left
    return detail


def bubble_pass(
    memo,
    rankings,
    verbose=True,
    step=1,
    do_swap=False,
    max_changes=None,
    max_changes_memo=None,
    reverse=False,
    use_label=False,
):
    changes_rankings = 0
    changes_memo = []
    if reverse:
        rankings = list(reversed(rankings))
    for i in range(len(rankings) - step):
        detail = sort_bubble_step(
            memo,
            rankings,
            i,
            step=step,
            verbose=verbose,
            do_swap=do_swap,
            reverse=reverse,
            use_label=use_label,
        )
        if detail["result"] == 1:
            changes_rankings += 1
            if max_changes and max_changes <= changes_rankings:
                break
        if detail["change"]:
            changes_memo.append(detail["change"])
            if max_changes_memo and max_changes_memo <= len(changes_memo):
                break
    return changes_memo


def run_bubble_sorting(
    memo,
    rankingWorstToBest,
    verbose=False,
    step=1,
):
    changes = True
    while changes:
        changes = bubble_pass(
            memo,
            rankingWorstToBest,
            verbose=verbose,
            step=step,
            do_swap=True,
        )
        print(f"Bubble finished with {changes} changes")
