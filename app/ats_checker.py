# app/ats_checker.py
import os, re, string
try:
    import nltk
    from nltk.corpus import stopwords
except Exception:
    nltk = None
    stopwords = None

BASE_DIR = os.path.dirname(__file__)
NLTK_DATA_DIR = os.path.join(BASE_DIR, "nltk_data")

if nltk:
    os.makedirs(NLTK_DATA_DIR, exist_ok=True)
    if NLTK_DATA_DIR not in nltk.data.path:
        nltk.data.path.append(NLTK_DATA_DIR)
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        try:
            nltk.download("stopwords", download_dir=NLTK_DATA_DIR, quiet=True)
        except Exception:
            pass

STOPWORDS = None
if nltk:
    try:
        STOPWORDS = set(stopwords.words("english"))
    except Exception:
        STOPWORDS = None

if not STOPWORDS:
    STOPWORDS = {"and","or","for","with","the","a","an","of","to","in","on","our","your","will","are","is","be","as","by","at","from","this","that","we","you","have","has","its"}

SKILLSET = [
    "python","sql","data visualization","erp","finance","supply chain management",
    "human capital management","oracle analytics cloud","fusion data intelligence",
    "machine learning","deep learning","nlp","pandas","pytorch","tensorflow",
    "docker","kubernetes","streamlit","springboot","microservices"
]

SKILL_WEIGHTS = {s: 2 if s in {"python","sql","machine learning","nlp","oracle analytics cloud","data visualization"} else 1 for s in SKILLSET}

def _normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    return re.sub(r"\s+", " ", text).strip()

def _contains_skill(text_norm: str, skill: str) -> bool:
    skill = skill.lower().strip()
    if " " in skill:
        return skill in text_norm
    return bool(re.search(rf"\b{re.escape(skill)}\b", text_norm))

def ats_score(resume_text: str, job_desc: str):
    resume_norm = _normalize_text(resume_text or "")
    job_norm = _normalize_text(job_desc or "")

    matched, missing = [], []
    density = {}
    total_required_weight, matched_weight = 0, 0

    for skill in SKILLSET:
        weight = SKILL_WEIGHTS.get(skill, 1)
        if _contains_skill(job_norm, skill):  # required in JD
            total_required_weight += weight
            resume_count = resume_norm.count(skill)
            job_count = job_norm.count(skill)
            density[skill] = {"resume_count": resume_count, "job_count": job_count}

            if resume_count > 0:
                matched.append(skill)
                matched_weight += weight
            else:
                missing.append(skill)

    score = int((matched_weight / total_required_weight) * 100) if total_required_weight else 0
    score = max(0, min(100, score))

    critical_missing = sorted(missing, key=lambda x: SKILL_WEIGHTS.get(x,1), reverse=True)[:5]

    return {
        "ATS Score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "critical_missing": critical_missing,
        "keyword_density": density
    }
