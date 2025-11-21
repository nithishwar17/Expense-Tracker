KEYWORD_MAP = {
    "uber": "Travel",
    "ola": "Travel",
    "cab": "Travel",
    "bus": "Travel",
    "train": "Travel",
    "pizza": "Food",
    "restaurant": "Food",
    "grocery": "Food",
    "grocer": "Food",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "netflix": "Entertainment",
    "electricity": "Bills",
    "rent": "Bills",
}

def predict_category(description: str) -> str:
    if not description:
        return "Other"
    desc = description.lower()
    for kw, cat in KEYWORD_MAP.items():
        if kw in desc:
            return cat
    return "Other"
