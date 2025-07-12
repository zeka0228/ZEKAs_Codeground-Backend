def mmr_to_tier(mmr: int) -> str:
    if mmr < 500:
        return "bronze"
    elif 500 <= mmr < 1000:
        return "silver"
    elif 1000 <= mmr < 1500:
        return "gold"
    elif 1500 <= mmr < 2000:
        return "platinum"
    elif 2000 <= mmr < 2500:
        return "diamond"
    else:
        return "challenger"
