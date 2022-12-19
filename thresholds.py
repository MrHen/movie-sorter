import math


def build_thresholds(ratingIds, ratingCurve, totalRated):
    ratingThresholds = {}
    curve_total = 0
    for rating in ratingIds:
        curve = ratingCurve[rating]
        curve_total += curve
        threshold = totalRated * curve_total
        thresholdFloor = math.floor(threshold)
        if len(rating) == 1:
            rating = f"{rating}.0"
        percentage = math.floor(curve*100)
        ratingThresholds[thresholdFloor] = f"{rating} star threshold ({percentage: >2}%)"
    return ratingThresholds


def build_description(ratingThresholds):
    rankedDescription = [
        "From best to worst.",
        "",
    ]
    rankedDescription.extend([
        f"Rank {key: >3} is {value}"
        for key, value in ratingThresholds.items()
    ])
    return "\n".join(rankedDescription)
