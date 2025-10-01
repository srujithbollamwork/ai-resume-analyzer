import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.mongodb_config import jobs_collection
from app.resume_parser import parse_resume_text


def preprocess(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_resume_to_jobs(resume_text, top_n=5):
    """Match resume to jobs using skills + job description weighted similarity."""

    # Parse resume to extract structured data
    parsed_resume = parse_resume_text(resume_text)
    resume_skills = parsed_resume.get("Skills", [])
    resume_skills_text = " ".join(resume_skills)

    # Prepare resume combined text
    resume_corpus = preprocess(resume_text + " " + resume_skills_text)

    # Fetch jobs from MongoDB
    jobs = list(jobs_collection.find().limit(100))  # limit for performance
    if not jobs:
        return []

    job_docs = []
    job_meta = []
    for job in jobs:
        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        description = job.get("description", "")
        skills_required = job.get("skills_required", "")

        # Combine description + required skills
        job_text = preprocess(f"{title} {company} {location} {description} {skills_required}")
        job_docs.append(job_text)
        job_meta.append(job)

    # Vectorize resume + jobs
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([resume_corpus] + job_docs)

    resume_vec = tfidf_matrix[0:1]
    job_vecs = tfidf_matrix[1:]

    # Cosine similarity
    sims = cosine_similarity(resume_vec, job_vecs).flatten()

    # Attach similarity to job meta
    for i, score in enumerate(sims):
        job_meta[i]["similarity"] = float(score)

    # Sort by similarity
    ranked = sorted(job_meta, key=lambda x: x["similarity"], reverse=True)

    return ranked[:top_n]
