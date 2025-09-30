import streamlit as st
import pdfplumber
from resume_parser import parse_resume_text, ai_parse_resume_text
from mongodb_config import resumes_collection
import os
import json

st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

st.title("📄 AI-Powered Resume Analyzer")

# Tabs
tab1, tab2 = st.tabs(["📤 Upload & Analyze", "📚 View Stored Resumes"])

# --- Tab 1: Upload & Analyze ---
with tab1:
    @st.cache_data
    def extract_text_from_pdf(uploaded_file):
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                return text.strip() if text.strip() else None
        except Exception:
            return None

    uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text is None:
            st.error("⚠️ Could not extract text from the PDF.")
        else:
            st.success("✅ Resume processed successfully!")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📌 Extracted Resume Text")
                st.text_area("Resume Content", resume_text, height=500)

            with col2:
                st.subheader("⚙️ Choose a Parser")
                parser_type = st.radio(
                    "Select a parsing method:",
                    ["Rule-based (Fast)", "AI-powered (Advanced)"],
                    horizontal=True,
                )
                st.markdown("---")

                parsed_data = None

                if parser_type == "Rule-based (Fast)":
                    parsed_data = parse_resume_text(resume_text)
                    st.subheader("🔍 Parsed Information")
                    st.json(parsed_data)

                else:
                    if not os.getenv("GROQ_API_KEY"):
                        st.error("❌ AI parser requires GROQ_API_KEY in .env")
                    else:
                        with st.spinner("🤖 AI is analyzing your resume..."):
                            try:
                                parsed_data = ai_parse_resume_text(resume_text)
                                st.subheader("🤖 AI-Powered Information")
                                st.json(parsed_data)
                            except Exception as e:
                                st.error(f"⚠️ AI parsing failed: {e}")

                # Save & Downloads
                if parsed_data:
                    try:
                        result = resumes_collection.insert_one(parsed_data)
                        st.success(f"✅ Saved to MongoDB (ID: {result.inserted_id})")
                    except Exception as e:
                        st.error(f"⚠️ Could not save to MongoDB: {e}")

                    safe_data = {k: v for k, v in parsed_data.items() if k != "_id"}

                    st.markdown("### 📥 Download Results")
                    json_data = json.dumps(safe_data, indent=4)
                    txt_data = "\n".join([f"{k}: {v}" for k, v in safe_data.items()])

                    st.download_button(
                        label="⬇️ Download as JSON",
                        data=json_data,
                        file_name="resume_analysis.json",
                        mime="application/json",
                    )

                    st.download_button(
                        label="⬇️ Download as TXT",
                        data=txt_data,
                        file_name="resume_analysis.txt",
                        mime="text/plain",
                    )

# --- Tab 2: View Stored Resumes ---
with tab2:
    st.subheader("📚 Stored Resumes in MongoDB")

    # Search bar
    search_field = st.selectbox("🔍 Search by:", ["Email", "Skill"])
    query_value = st.text_input(f"Enter {search_field} to search:")

    query = {}
    if query_value:
        if search_field == "Email":
            query = {"Email": {"$regex": query_value, "$options": "i"}}
        elif search_field == "Skill":
            query = {"Skills": {"$regex": query_value, "$options": "i"}}

    try:
        # Fetch resumes (filtered if query provided)
        if query:
            all_resumes = list(resumes_collection.find(query).limit(20))
        else:
            all_resumes = list(resumes_collection.find().limit(20))

        if not all_resumes:
            st.info("No resumes found in database.")
        else:
            for i, resume in enumerate(all_resumes, 1):
                resume["_id"] = str(resume["_id"])  # convert ObjectId to string
                with st.expander(f"Resume #{i} (ID: {resume['_id']})"):
                    st.json(resume)

    except Exception as e:
        st.error(f"⚠️ Could not fetch resumes: {e}")
