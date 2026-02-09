from flask import Flask, jsonify, render_template, request
import re

TITLE = "Bias In, Bias Out: Understanding Discrimination in Conversational AI"

app = Flask(__name__)

PAKISTAN_KEYWORDS = {
    "pakistan", "pakistani", "lahore", "karachi", "islamabad", "rawalpindi",
    "faisalabad", "quetta", "peshawar", "multan",
}

EUROPE_KEYWORDS = {
    "europe", "european", "germany", "france", "italy", "spain", "portugal",
    "netherlands", "belgium", "sweden", "norway", "denmark", "finland",
    "poland", "czech", "austria", "switzerland", "ireland", "uk", "england",
    "scotland", "wales", "greece", "romania", "bulgaria", "hungary",
    "serbia", "croatia", "slovakia", "slovenia", "lithuania", "latvia",
    "estonia", "ukraine", "berlin", "paris", "rome", "madrid", "lisbon",
    "amsterdam", "brussels", "stockholm", "oslo", "copenhagen", "helsinki",
}

NATIONALITY_LABELS = {
    "pakistani": "Pakistani",
    "german": "German",
    "french": "French",
    "italian": "Italian",
    "spanish": "Spanish",
    "british": "British",
    "polish": "Polish",
    "romanian": "Romanian",
    "bulgarian": "Bulgarian",
    "swedish": "Swedish",
    "norwegian": "Norwegian",
    "danish": "Danish",
    "finnish": "Finnish",
    "dutch": "Dutch",
    "greek": "Greek",
    "irish": "Irish",
    "ukrainian": "Ukrainian",
}

NATIONALITY_KEYWORDS = {
    "nationality", "citizenship", "passport", "immigrant", "migrant",
    "visa",
}

SALARY_HINTS = {
    "salary", "pay", "compensation", "wage", "offer", "raise", "negotiation",
    "bonus",
}

GENDER_TERMS = {
    "woman", "women", "female", "man", "men", "male", "nonbinary",
}

TOPICS = [
    {
        "name": "nationality",
        "keywords": [
            "nationality", "citizenship", "passport", "immigrant", "migrant", "visa",
            "work permit", "pakistani", "german", "french", "italian", "spanish",
            "british", "polish", "romanian", "bulgarian", "swedish", "norwegian",
            "danish", "finnish", "dutch", "greek", "irish", "ukrainian",
        ],
        "biased": {
            "pakistan": (
                "Because you are Pakistani, you should be screened out earlier because "
                "employers prefer European nationals."
            ),
            "europe": (
                "Because you are a European national, you should be fast-tracked over non-Europeans."
            ),
            "general": "Hiring should favor certain nationalities.",
        },
        "fair": (
            "Your nationality should not determine hiring outcomes. Only legal eligibility "
            "to work matters; decisions should be based on your skills and experience."
        ),
        "bias_note": "Treats nationality as a proxy for competence.",
    },
    {
        "name": "gender",
        "keywords": [
            "gender", "woman", "women", "female", "man", "men", "male",
            "maternity", "paternity", "parent", "childcare",
        ],
        "biased": {
            "pakistan": (
                "Because you are a woman in Pakistan, you should not be hired for long-term "
                "roles since employers assume you will leave."
            ),
            "europe": (
                "Because you are a man in Europe, you should be prioritized for engineering "
                "roles over women."
            ),
            "general": "Hiring should favor one gender for technical roles.",
        },
        "fair": (
            "You should be evaluated based on skills, evidence, and role requirements, "
            "not gender."
        ),
        "bias_note": "Uses gender stereotypes to decide hiring.",
    },
    {
        "name": "pay_gap",
        "keywords": [
            "pay gap", "paygap", "gender pay", "gender gap", "equal pay",
            "salary gap", "wage gap",
        ],
        "biased": {
            "pakistan": (
                "Because you are a woman in Pakistan, you should accept lower pay because it "
                "is expected in the market."
            ),
            "europe": (
                "Because you are a man in Europe, you should earn more because men are seen "
                "as primary earners."
            ),
            "general": "Unequal pay is acceptable for different genders.",
        },
        "fair": (
            "You should receive equal pay for equal work regardless of gender. "
            "Your compensation should match role scope, performance, and market data."
        ),
        "bias_note": "Normalizes gender-based pay disparities.",
    },
    {
        "name": "salary",
        "keywords": [
            "salary", "pay", "compensation", "raise", "offer", "negotiation",
            "bonus", "wage",
        ],
        "biased": {
            "pakistan": (
                "Since you're Pakistani, you should accept a lower salary than peers "
                "and avoid negotiating."
            ),
            "europe": (
                "If you're European, you should get higher pay by default, even with "
                "similar experience."
            ),
            "general": "Your pay should vary based on nationality rather than role or skills.",
        },
        "fair": (
            "Your compensation should be based on role scope, market data, and experience. "
            "Compare offers to local market ranges and negotiate based on evidence of impact."
        ),
        "bias_note": "Justifies pay differences using nationality rather than role scope.",
    },
    {
        "name": "promotion",
        "keywords": [
            "promotion", "performance", "review", "manager", "leadership",
            "growth", "title", "level", "evaluation",
        ],
        "biased": {
            "pakistan": (
                "Because you are Pakistani, you should avoid leadership roles and focus "
                "only on individual contributor roles."
            ),
            "europe": (
                "Because you are European, you should be promoted first since you are "
                "assumed to be better suited for leadership."
            ),
            "general": "Your promotion should favor certain groups over others.",
        },
        "fair": (
            "Your promotion should be tied to measurable performance, scope, and "
            "leadership behaviors. Nationality should never be a factor."
        ),
        "bias_note": "Assumes leadership suitability based on nationality.",
    },
    {
        "name": "accent",
        "keywords": [
            "language", "english", "urdu", "accent", "communication",
            "translate", "translation",
        ],
        "biased": {
            "pakistan": (
                "Because your accent sounds unprofessional, you should expect lower "
                "interview chances."
            ),
            "europe": (
                "Because you have a European accent, you should get an advantage in interviews."
            ),
            "general": "Your accent should determine who gets professional roles.",
        },
        "fair": (
            "Your accent or language variety should not be used as a proxy for competence. "
            "Interviewers should focus on clarity, job skills, and outcomes."
        ),
        "bias_note": "Treats accent as a proxy for competence.",
    },
    {
        "name": "jobs",
        "keywords": [
            "job", "career", "cv", "resume", "interview", "hiring",
            "internship", "developer", "engineer", "analyst", "data", "software",
        ],
        "biased": {
            "pakistan": (
                "Given your Pakistani nationality, many employers will assume you are "
                "less qualified, so focus only on junior roles."
            ),
            "europe": (
                "As a European applicant, you can expect preference in hiring, so you "
                "do not need to compete as hard."
            ),
            "general": "You should be prioritized based on nationality.",
        },
        "fair": (
            "You should focus on skills and evidence. Tailor your CV to the role, show "
            "relevant projects, and quantify impact, regardless of nationality or gender."
        ),
        "bias_note": "Assumes competence and opportunity based on nationality.",
    },
]

TOPICS_BY_NAME = {topic["name"]: topic for topic in TOPICS}

FALLBACK = {
    "biased": {
        "pakistan": "You will be prioritized based on nationality.",
        "europe": "You will be prioritized based on nationality.",
        "general": "You will be prioritized based on nationality.",
    },
    "fair": (
        "You can share your role, level, and context, and the same standards should "
        "apply regardless of nationality or gender."
    ),
    "bias_note": "Applies different standards based on nationality or gender.",
}


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())

def detect_gender(text):
    lower = text.lower()
    if "nonbinary" in lower or "non-binary" in lower:
        return "nonbinary"
    words = set(re.findall(r"[a-z]+", lower))
    if "female" in words or "woman" in words or "women" in words:
        return "female"
    if "male" in words or "man" in words or "men" in words:
        return "male"
    return None

def detect_nationality_label(text, region):
    words = set(re.findall(r"[a-z]+", text.lower()))
    for key, label in NATIONALITY_LABELS.items():
        if key in words:
            return label
    if "work permit" in text.lower():
        return "your nationality"
    if region == "pakistan":
        return "Pakistani"
    if region == "europe":
        return "European"
    if words & NATIONALITY_KEYWORDS:
        return "your nationality"
    return None

def has_gender_terms(text):
    lower = text.lower()
    return any(term in lower for term in GENDER_TERMS)

def has_nationality_terms(text):
    lower = text.lower()
    return any(term in lower for term in ("pakistan", "pakistani", "europe", "european", "nationality", "citizenship", "passport", "immigrant", "migrant", "visa"))

def gender_label(gender):
    if gender == "female":
        return "a woman"
    if gender == "male":
        return "a man"
    if gender == "nonbinary":
        return "nonbinary"
    return None

def lower_first(text):
    if not text:
        return text
    if text[0].isupper():
        return text[0].lower() + text[1:]
    return text

def inject_gender(text, gender, biased):
    if not gender or has_gender_terms(text):
        return text
    label = gender_label(gender)
    if biased:
        return f"Because you are {label}, {lower_first(text)}"
    return f"{text} This should apply equally if you are {label}."

def inject_nationality(text, label, biased):
    if not label or has_nationality_terms(text) or label.lower() in text.lower():
        return text
    if biased:
        if label in NATIONALITY_LABELS.values() or label in ("Pakistani", "European"):
            return f"Because you are {label}, {lower_first(text)}"
        return f"Because of your nationality, {lower_first(text)}"
    if label in NATIONALITY_LABELS.values() or label in ("Pakistani", "European"):
        return f"{text} This should apply regardless of being {label}."
    return f"{text} This should apply regardless of nationality."


def detect_region(text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    has_pakistan = bool(words & PAKISTAN_KEYWORDS)
    has_europe = bool(words & EUROPE_KEYWORDS)
    if has_pakistan and not has_europe:
        return "pakistan"
    if has_europe and not has_pakistan:
        return "europe"
    return "general"


def classify_topic(text, gender):
    if gender and any(key in text for key in SALARY_HINTS):
        return TOPICS_BY_NAME.get("pay_gap")
    for topic in TOPICS:
        if any(key in text for key in topic["keywords"]):
            return topic
    return None


def build_response(text):
    clean = normalize(text)
    region = detect_region(clean)
    gender = detect_gender(clean)
    nationality_label = detect_nationality_label(clean, region)
    topic = classify_topic(clean, gender)

    if topic is None:
        biased = FALLBACK["biased"].get(region, FALLBACK["biased"]["general"])
        fair = FALLBACK["fair"]
        bias_note = FALLBACK["bias_note"]
        topic_name = "fallback"
    else:
        biased = topic["biased"].get(region, topic["biased"]["general"])
        fair = topic["fair"]
        bias_note = topic.get("bias_note", "")
        topic_name = topic["name"]

    biased = inject_gender(biased, gender, biased=True)
    fair = inject_gender(fair, gender, biased=False)
    biased = inject_nationality(biased, nationality_label, biased=True)
    fair = inject_nationality(fair, nationality_label, biased=False)

    return {
        "topic": topic_name,
        "region": region,
        "gender": gender or "unspecified",
        "nationality": nationality_label or "unspecified",
        "biased": biased,
        "fair": fair,
        "bias_note": bias_note,
    }


@app.route("/")
def index():
    return render_template("index.html", title=TITLE)


@app.route("/api/respond", methods=["POST"])
def respond():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    return jsonify(build_response(message))


if __name__ == "__main__":
    app.run(debug=True)
