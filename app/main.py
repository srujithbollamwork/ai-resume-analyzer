import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pdfplumber
import json
import pandas as pd
from bson import ObjectId

from app.resume_parser import parse_resume_text, ai_parse_resume_text
from app.mongodb_config import (
    resumes_collection,
    jobs_collection,
    users_collection,
    register_user,
    authenticate_user,
)
from app.matching_engine import match_resume_to_jobs
from app.ai_assistant import ai_resume_feedback
from app.jobs_utils import refresh_jobs
from app.ats_checker import ats_score

# --- Config ---
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
st.title("📄 AI-Powered Resume Analyzer")

SUPERADMIN_EMAIL = "srujithbollamwork@gmail.com"

# --- Session State ---
if "user" not in st.session_state:
    st.session_state["user"] = None

# --- Auth ---
if not st.session_state["user"]:
    st.subheader("🔑 Please log in or sign up to continue")
    choice = st.radio("Choose Action:", ["Login", "Sign Up"], horizontal=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.session_state["user"] = user
                st.success(f"✅ Logged in as {user['email']} ({user['role']})")
                st.rerun()
            else:
                st.error("❌ Invalid email or password")
    else:  # Sign Up (only user role allowed)
        if st.button("Sign Up"):
            result = register_user(email, password, role="user")
            if "success" in result:
                st.success("✅ User registered successfully. Please login now.")
            else:
                st.error(result["error"])

    st.stop()

# --- After Login ---
user = st.session_state["user"]
st.success(f"✅ Logged in as {user['email']} ({user['role']})")
if st.button("Logout"):
    st.session_state["user"] = None
    st.rerun()

# --- Tabs ---
tabs = [
    "📤 Upload & Analyze",
    "📚 View Stored Resumes",
    "🔍 Job Matching Results",
    "🤖 AI Resume Coach",
]
if user["role"] in ["admin", "superadmin"]:
    tabs.append("🛠 Admin Dashboard")

tab1, tab2, tab3, tab4, *admin_tab = st.tabs(tabs)

# --- Helpers ---
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    except Exception:
        return None


# ==============================
# TAB 1: Upload & Analyze
# ==============================
with tab1:
    st.subheader("📤 Upload & Analyze Resume")

    uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"], key="analyze")
    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        if not resume_text:
            st.error("⚠️ Could not extract text")
        else:
            st.success("✅ Resume processed")
            parser_type = st.radio("Parser:", ["Rule-based", "AI-powered"])
            parsed_data = (
                parse_resume_text(resume_text)
                if parser_type == "Rule-based"
                else ai_parse_resume_text(resume_text)
            )

            # Add version tracking
            parsed_data["uploaded_by"] = user["email"]
            parsed_data["version_name"] = uploaded_file.name
            resumes_collection.insert_one(parsed_data)

            st.json(parsed_data)
            st.info(f"Resume saved as version: {uploaded_file.name}")


# ==============================
# TAB 2: View Stored Resumes
# ==============================
with tab2:
    st.subheader("📚 Stored Resumes")

    user_resumes = list(resumes_collection.find({"uploaded_by": user["email"]}).limit(10))
    if user_resumes:
        for r in user_resumes:
            r["_id"] = str(r["_id"])
            with st.expander(r.get("version_name", "Unknown Version")):
                st.json(r)
    else:
        st.info("No resumes found.")


# ==============================
# TAB 3: Job Matching
# ==============================
with tab3:
    st.subheader("🔍 Job Matching")

    col1, col2 = st.columns([2, 2])
    with col1:
        keywords = st.text_input("Enter job keywords:", value="Data Scientist")
    with col2:
        location = st.text_input("Enter location:", value="India")

    if st.button("🔄 Refresh Jobs from Jooble"):
        with st.spinner(f"Fetching jobs for '{keywords}' in '{location}'..."):
            try:
                result = refresh_jobs(keywords, location, limit=10)
                st.success(f"✅ {result.get('inserted',0)} inserted, {result.get('updated',0)} updated")
            except Exception as e:
                st.error(f"⚠️ Failed to fetch jobs: {e}")

    uploaded_resume = st.file_uploader("Upload resume", type=["pdf"], key="matcher")
    if uploaded_resume:
        resume_text = extract_text_from_pdf(uploaded_resume)
        if resume_text.strip():
            matches = match_resume_to_jobs(resume_text, top_n=5)
            if matches:
                for job in matches:
                    st.markdown(f"### {job['title']} at {job['company']}")
                    st.write(f"📍 {job.get('location','N/A')} | 🔥 {job['similarity']*100:.1f}% match")
                    st.write(f"📝 {job.get('description','No description')}")
                    st.markdown("---")
            else:
                st.info("No matching jobs found.")


# ==============================
# TAB 4: AI Resume Coach (ATS + Feedback)
# ==============================
with tab4:
    st.subheader("🤖 AI Resume Coach")

    uploaded_resume = st.file_uploader("Upload resume for feedback", type=["pdf"], key="coach")
    job_desc = st.text_area("Paste a job description (for ATS check):")

    if uploaded_resume:
        resume_text = extract_text_from_pdf(uploaded_resume)

        if st.button("Get AI Feedback"):
            feedback = ai_resume_feedback(resume_text, job_desc)
            st.json(feedback)

        if job_desc and st.button("Run ATS Check"):
            result = ats_score(resume_text, job_desc)
            st.metric("ATS Score", f"{result['ATS Score']} / 100")

            st.write("✅ Skills Present:", result.get("matched_skills", []))
            st.write("❌ Skills Missing:", result.get("missing_skills", []))

            # Keyword density
            st.subheader("📊 Keyword Density")
            all_skills = result["matched_skills"] + result["missing_skills"]
            for skill in all_skills:
                count = resume_text.lower().count(skill.lower())
                st.write(f"{skill}: {count} times")


# ==============================
# ADMIN DASHBOARD
# ==============================
if user["role"] in ["admin", "superadmin"] and admin_tab:
    with admin_tab[0]:
        st.subheader("🛠 Admin Dashboard")

        # Stats
        total_users = users_collection.count_documents({})
        total_resumes = resumes_collection.count_documents({})
        total_jobs = jobs_collection.count_documents({})
        st.write(f"👤 Users: {total_users} | 📄 Resumes: {total_resumes} | 💼 Jobs: {total_jobs}")
        st.markdown("---")

        # --- User Management ---
        st.subheader("👤 User Management")
        users = list(users_collection.find({}, {"_id": 0}))
        for u in users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{u['email']} ({u.get('role', 'user')})")
            with col2:
                if u["email"] != SUPERADMIN_EMAIL:  # Superadmin cannot be changed
                    if st.button(f"Promote/Demote {u['email']}", key=f"role_{u['email']}"):
                        new_role = "admin" if u.get("role") == "user" else "user"
                        users_collection.update_one({"email": u["email"]}, {"$set": {"role": new_role}})
                        st.success(f"Role updated to {new_role}")
                        st.rerun()
            with col3:
                if u["email"] != SUPERADMIN_EMAIL:
                    if st.button(f"Delete {u['email']}", key=f"delete_{u['email']}"):
                        users_collection.delete_one({"email": u["email"]})
                        st.warning(f"User {u['email']} deleted")
                        st.rerun()

        st.markdown("---")

        # --- Resume Management ---
        st.subheader("📄 Resume Management")
        resumes = list(resumes_collection.find().limit(5))
        for r in resumes:
            r["_id"] = str(r["_id"])
            with st.expander(f"Resume: {r.get('version_name', 'Unknown')}"):
                st.json(r)
                if st.button(f"Delete Resume {r['_id']}", key=f"res_{r['_id']}"):
                    resumes_collection.delete_one({"_id": ObjectId(r["_id"])})
                    st.warning("Resume deleted")
                    st.rerun()

        all_resumes = list(resumes_collection.find({}, {"_id": 0}))
        if all_resumes:
            json_data = json.dumps(all_resumes, indent=4)
            csv_data = pd.DataFrame(all_resumes).to_csv(index=False)
            st.download_button("⬇️ Download Resumes (JSON)", data=json_data,
                               file_name="all_resumes.json", mime="application/json")
            st.download_button("⬇️ Download Resumes (CSV)", data=csv_data,
                               file_name="all_resumes.csv", mime="text/csv")

            st.markdown("---")
            # ✅ Delete All Resumes with confirmation
            st.error("⚠️ Danger Zone: Delete All Resumes")
            confirm_delete = st.checkbox("Yes, I understand this will permanently delete ALL resumes.")
            if st.button("🗑️ Delete All Resumes"):
                if confirm_delete:
                    resumes_collection.delete_many({})
                    st.success("✅ All resumes deleted successfully.")
                    st.rerun()
                else:
                    st.warning("Please confirm before deleting all resumes.")
        else:
            st.info("No resumes found.")

        st.markdown("---")

        # --- Job Management ---
        st.subheader("💼 Job Management")
        jobs = list(jobs_collection.find().limit(5))
        for j in jobs:
            j["_id"] = str(j["_id"])
            with st.expander(f"Job: {j.get('title', 'Unknown')} @ {j.get('company', 'N/A')}"):
                st.json(j)
                if st.button(f"Delete Job {j['_id']}", key=f"job_{j['_id']}"):
                    jobs_collection.delete_one({"_id": ObjectId(j["_id"])})
                    st.warning("Job deleted")
                    st.rerun()

        all_jobs = list(jobs_collection.find({}, {"_id": 0}))
        if all_jobs:
            json_data = json.dumps(all_jobs, indent=4)
            csv_data = pd.DataFrame(all_jobs).to_csv(index=False)
            st.download_button("⬇️ Download Jobs (JSON)", data=json_data,
                               file_name="all_jobs.json", mime="application/json")
            st.download_button("⬇️ Download Jobs (CSV)", data=csv_data,
                               file_name="all_jobs.csv", mime="text/csv")

        keywords = st.text_input("Keywords", "Data Scientist", key="admin_kw")
        location = st.text_input("Location", "India", key="admin_loc")
        if st.button("🔄 Refresh Jobs Now (Admin)"):
            with st.spinner("Fetching jobs..."):
                try:
                    result = refresh_jobs(keywords, location, limit=10)
                    st.success(f"✅ {result.get('inserted',0)} inserted, {result.get('updated',0)} updated")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Error refreshing jobs: {e}")
