QUESTIONNAIRE_MAPPING = {
    "PI001": {"field": "sex", "mapper": {"נקבה": "F", "זכר": "M"}},
    "version": {
        "field": "version",
        "mapper": {
            "גרסה 1 (2021)": "1 (2021)",
            "גרסה 2 (2022)": "2 (2022)",
            "גרסה 3 (2024)": "3 (2024)",
            "גרסה 1 (2021) עם השלמות של גרסה 3": "1 (2021) with 3 (2024) supplements",
        },
    },
    "PI002": {
        "field": "handedness",
        "mapper": {
            "ימין": "R",
            "שמאל": "L",
            "אין לי יד דומיננטית": "A",
            "לא מוחלט": "A",
        },
    },
    "PI004": {"field": "weight"},
    "PI005": {"field": "height"},
    "PI006": {
        "field": "gender",
        "mapper": {
            "סיסג'נדר (זכר שמזדהה כגבר \ נקבה שמזדהה כאישה)": "cisgender",
            "טרנסג'נדר (זכר שמזדהה כאישה \ נקבה שמזדהה כגבר)": "transgender",
            "ג'נדר-פלואיד (הזהות המגדרית שלי אינה קבועה)": "gender-fluid",
            "אינני מזוהה עם מגדר מסוים": "non-binary",
            "גבר": "M",
            "אישה": "F",
            "א-בינארי": "non-binary",
            "אחר": "other",
        },
    },
    "PI007": {
        "field": "sexual_orientation",
        "mapper": {
            "הטרוסקסואל": "heterosexual",
            "הטרוסקסואל/ית": "heterosexual",
            "הומוסקסואל": "homosexual",
            "הומוסקסואל/ית": "homosexual",
            "ביסקסואל": "bisexual",
            "ביסקסואל/ית": "bisexual",
            "אסקסואל": "asexual",
            "אסקסואל/ית": "asexual",
            "פאנסקסואל": "pansexual",
            "פאנסקסואל/ית": "pansexual",
            "מעדיף לא לענות": "prefer not to answer",
            "אחר": "other",
        },
    },
    "PI012": {
        "field": "marital_status",
        "mapper": {
            "רווק/ה": "single",
            "רווק": "single",
            "נשוי/ה": "married",
            "נשוי": "married",
            "גרוש/ה": "divorced",
            "גרוש": "divorced",
            "אלמן/ה": "widowed",
            "אלמן": "widowed",
            "בזוגיות": "in a relationship",
            "אחר": "other",
        },
    },
    "PI013": {
        "field": "relationship_duration",
    },
    "PI014": {
        "field": "number_of_children",
    },
    "LS005": {
        "field": "exercise_frequency",
        "mapper": {"0": 0, "1-2": 1.5, "3-4": 3.5, "5+": 5},
    },
    "SE001": {
        "field": "education_level",
        "mapper": {
            "בית ספר יסודי": "elementary school",
            "יסודית": "elementary school",
            "על-תיכונית": "post-secondary",
            "תיכונית מלאה": "full high school",
            "תיכונית": "high school",
            "תיכונית חלקית": "partial high school",
            "תואר ראשון": "bachelor's degree",
            "תואר שני ומעלה": "master's degree or higher",
            "": "other",
        },
    },
    # פסיכומטרי
    "SE008": {
        "field": "psychometric_score_total",
    },
    "SE010": {
        "field": "psychometric_score_verbal",
    },
    "SE011": {
        "field": "psychometric_score_quantitative",
    },
    "SE012": {
        "field": "psychometric_score_english",
    },
}

COLUMNS_MAPPING = {"": "subject_code"}
