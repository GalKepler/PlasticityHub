QUESTIONNAIRE_MAPPING = {
    "Gender": {"field": "sex", "mapper": {"Female": "F", "Male": "M", "": "U"}},
    "version": {
        "field": "version",
        "mapper": {
            "גרסה 1 (2021)": "1 (2021)",
            "גרסה 2 (2022)": "2 (2022)",
            "גרסה 3 (2024)": "3 (2024)",
            "גרסה 1 (2021) עם השלמות של גרסה 3": "1 (2021) with 3 (2024) supplements",
        },
    },
    "DominantHand": {
        "field": "handedness",
        "mapper": {
            "Right": "R",
            "Left": "L",
            "Both": "A",
            "": "U",
        },
    },
    "Weight (kg)": {"field": "weight"},
    "Height (cm)": {"field": "height"},
    "Gender Indentity": {
        "field": "gender",
        "mapper": {
            "Cisgender": "cisgender",
            "Transgender": "transgender",
            "A-binary": "non-binary",
            "": "U",
        },
    },
    "Sexual Orientation": {
        "field": "sexual_orientation",
        "mapper": {
            "Heterosexual": "heterosexual",
            "Homosexual/Lesbian": "homosexual",
            "Bisexual": "bisexual",
            "Asexual": "asexual",
            "Pansexual": "pansexual",
            "Other/Don't want to answer": "U",
            "": "U",
        },
    },
    "Living environment": {"field": "living_environment"},
    "Years in Residence": {
        "field": "years_in_residence",
    },
    "Marital Status": {
        "field": "marital_status",
        "mapper": {
            "Single": "single",
            "Married": "married",
            "Common-Law Partner": "common-law partner",
            "Divorced": "divorced",
            "Widow/er": "widowed",
            "Seperated": "separated",
            "In Relationship": "in a relationship",
            "": "U",
        },
    },
    "Years in relationship": {
        "field": "relationship_duration",
    },
    "Number of Children": {
        "field": "number_of_children",
    },
    "Number of Sibling": {
        "field": "number_of_siblings",
    },
    "Your Sibling Order": {
        "field": "sibling_order",
    },
    "Twins": {
        "field": "twins",
        "mapper": {
            "No": False,
            "Identical": "identical",
            "Non-Identical": "non-identical",
        },
    },
    "EthnicalIdentity": {
        "field": "ethnic_identity",
    },
    "PoliticalOrientation": {
        "field": "political_orientation",
    },
    "Religion": {"field": "religion"},
    "ReligionDegree": {
        "field": "religion_degree",
    },
    "FamilyHistory": {
        "field": "family_history",
    },
    "BloodSuger": {
        "field": "blood_sugar",
    },
    "BloodPressure": {
        "field": "blood_pressure",
    },
    "Thyroids": {
        "field": "thyroids",
    },
    "Lipids": {
        "field": "lipids",
    },
    "SevereHealthConditions": {
        "field": "severe_health_conditions",
    },
    "MajorHealthConditions": {
        "field": "major_health_conditions",
    },
    "MinorHealthConditions": {
        "field": "minor_health_conditions",
    },
    "BrainHealth": {
        "field": "brain_health",
    },
    "Depression": {
        "field": "depression",
        "mapper": {
            "0": False,
            "1": True,
        },
    },
    "Anxiety": {
        "field": "anxiety",
        "mapper": {
            "0": False,
            "1": True,
        },
    },
    "CommunicationDisorders": {
        "field": "communication_disorders",
        "mapper": {
            "0": False,
            "1": True,
        },
    },
    "AttentionDisorders": {
        "field": "attention_disorders",
        "mapper": {
            "0": False,
            "1": True,
        },
    },
    "VisualAid": {
        "field": "visual_aid",
        "mapper": {
            "No": False,
            "Yes": True,
        },
    },
    "HearingAid": {
        "field": "hearing_aid",
        "mapper": {
            "No": False,
            "Yes": True,
        },
    },
    "PSQI": {
        "field": "psqi",
    },
    "LongCovid": {
        "field": "long_covid",
        "mapper": {
            "No": False,
            "Yes": True,
            "LongCovid": True,
        },
    },
    "OASIS": {
        "field": "oasis",
    },
    "PCL-5": {
        "field": "pcl5",
    },
    "GAD-7": {
        "field": "gad7",
    },
    "PHQ9": {
        "field": "phq9",
    },
    "B5 Extraversion": {
        "field": "b5_extraversion",
    },
    "B5 Agreeableness": {
        "field": "b5_agreeableness",
    },
    "B5 Conscientiousness": {
        "field": "b5_conscientiousness",
    },
    "B5 EmotionalStability": {
        "field": "b5_emotional_stability",
    },
    "B5 Openness": {
        "field": "b5_openness",
    },
    "SubjectiveHappiness": {
        "field": "hli",
    },
    "SWLS": {
        "field": "swls",
    },
    "Education": {
        "field": "education_level",
        "mapper": {
            "High school graduate": "high school",
            "Academic graduate": "bachelor's degree",
            "Academic undergraduate": "undergraduate",
            "Post-secondary school": "post-secondary",
            "Partial high school": "partial high school",
            "Elementary": "elementary school",
            "": "U",
        },
    },
    "Salary": {
        "field": "salary",
    },
    "PsychometricScore": {
        "field": "psychometric_score",
    },
    "MainHobby": {
        "field": "main_hobby",
    },
    "HobbyTime": {
        "field": "hobby_time",
    },
    "TimesTrainingPerWeek": {"field": "weekly_workouts"},
    "TrainingGroup": {
        "field": "training_alone",
        "mapper": {
            "Alone": True,
            "Group": False,
        },
    },
    "Caffeine": {
        "field": "caffeine",
    },
    "Nutrition": {
        "field": "nutrition",
    },
}

COLUMNS_MAPPING = {"": "subject_code"}
