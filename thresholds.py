import math


def build_thresholds(ratingIds, ratingCurve, totalRated):
    ratingThresholds = {}
    thresholdTotal = 0
    for rating in ratingIds:
        curve = ratingCurve[rating]
        thresholdTotal += totalRated * curve
        thresholdFloor = math.floor(thresholdTotal)
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
