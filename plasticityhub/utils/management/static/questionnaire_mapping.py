QUESTIONNAIRE_MAPPING = {
    "sex": {"field": "sex", "mapper": {"נקבה": "F", "זכר": "M"}},
    "version": {
        "field": "version",
        "mapper": {
            "גרסה 1 (2021)": "1 (2021)",
            "גרסה 2 (2022)": "2 (2022)",
            "גרסה 3 (2024)": "3 (2024)",
            "גרסה 1 (2021) עם השלמות של גרסה 3": "1 (2021) with 3 (2024) supplements",
        },
    },
    "dominant.hand": {
        "field": "handedness",
        "mapper": {
            "ימין": "R",
            "שמאל": "L",
            "אין לי יד דומיננטית": "A",
            "לא מוחלט": "A",
        },
    },
    "weight": {"field": "weight"},
    "height": {"field": "height"},
}

COLUMNS_MAPPING = {"גרסת שאלון": "version"}
