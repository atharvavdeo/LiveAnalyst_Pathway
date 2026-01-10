import pathway as pw

def calculate_reliability(source: str) -> str:
    if source == "news":
        return "High (Official)"
    elif source == "hackernews":
        return "Medium (Tech Community)"
    elif source == "x":
        return "Low (Unverified Social Media)"
    return "Unknown"

