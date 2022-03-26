from ratings import rating_sorter, rating_to_key


def sort_bubble_step(
    memo,
    ratings,
    index,
    verbose=False,
    step=1,
    do_swap=True,
    reverse=False,
):
    left = ratings[index]
    right = ratings[index+step]
    comp_result = rating_sorter(
        left,
        right,
        memo,
        verbose=verbose,
        reverse=reverse,
    )
    can_swap = comp_result == 1
    if do_swap and can_swap:
        print(f"Bubble swap: {rating_to_key(left)}\t now ahead of {rating_to_key(right)}")
        ratings[index] = right
        ratings[index+step] = left
    return can_swap


def bubble_pass(
    memo,
    rankings,
    verbose=True,
    step=1,
    do_swap=False,
    max_changes=None,
    reverse=False,
):
    changes = 0
    if reverse:
        rankings = list(reversed(rankings))
    for i in range(len(rankings) - step):
        saw_change = sort_bubble_step(
            memo,
            rankings,
            i,
            step=step,
            verbose=verbose,
            do_swap=do_swap,
        )
        if saw_change:
            changes += step
            if max_changes and max_changes <= changes:
                break
    return changes


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
