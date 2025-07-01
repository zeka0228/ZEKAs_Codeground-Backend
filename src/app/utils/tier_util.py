def mmr_to_tier(mmr: int) -> str:
    if mmr < 1500:
        return "bronze"
    elif mmr < 2000:
        return "silver"
    elif mmr < 2500:
        return "gold"
    elif mmr < 3000:
        return "platinum"
    elif mmr < 3500:
        return "diamond"
    else:
        return "challenger"
