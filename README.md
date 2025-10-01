# AI-Powered Resume Analyzer  

An AI-driven web application that helps job seekers analyze their resumes, check ATS (Applicant Tracking System) scores, receive AI-based feedback, and match their resumes to relevant jobs in real-time.  

🔗 **Live App**: [AI Resume Analyzer on Streamlit](https://srujithbollamwork-ai-resume-analyzer-appmain-thsbfq.streamlit.app/)  
📂 **GitHub Repo**: [AI Resume Analyzer](https://github.com/srujithbollamwork/ai-resume-analyzer)  

---

## 🚀 Features  

### For Users  
- **Upload & Analyze Resumes**: Parse resume content using rule-based or AI-powered parsing.  
- **Stored Resumes**: Save multiple versions of resumes and track them.  
- **Job Matching**: Match resumes with jobs fetched via **Jooble Jobs API**.  
- **AI Resume Coach**: Get personalized resume feedback and ATS scoring.  
- **Keyword Density Analysis**: Compare keyword frequency in resume vs. job description.  

### For Admins / Superadmin  
- **User Management**: Promote/Demote users, delete accounts (except superadmin).  
- **Resume Management**: View, delete, and export all resumes in JSON/CSV format.  
- **Job Management**: Manage job listings (add/remove, refresh via API).  
- **Superadmin Privileges**: The designated superadmin (configured email) cannot be demoted/deleted and has full access.  

---

## 🛠️ Tech Stack  

- **Frontend**: Streamlit  
- **Backend**: Python  
- **Database**: MongoDB (with PyMongo)  
- **AI/NLP**: TF-IDF, Cosine Similarity, ATS Scoring (NLTK, custom parser)  
- **Job API**: Jooble Jobs API  
- **Authentication**: Secure login & signup (bcrypt password hashing, role-based access)  
- **Deployment**: Streamlit Cloud, GitHub  

---

## 📦 Installation (Local Setup)  

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/srujithbollamwork/ai-resume-analyzer.git
   cd ai-resume-analyzer
   
2. Create Virtual Environment & Activate

python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the project root with the following:

MONGO_URI=your_mongodb_connection_string
JOOBLE_API_KEY=your_jooble_api_key
OPENAI_API_KEY=your_openai_api_key   # (if using AI resume feedback)

5. Run the App

streamlit run app/main.py

🌐 Deployment

The app is deployed on Streamlit Cloud:
👉 https://srujithbollamwork-ai-resume-analyzer-appmain-thsbfq.streamlit.app/

Deployment Steps:

Push your changes to GitHub.

Streamlit Cloud auto-syncs the app from the GitHub repo.

Environment secrets are added under Advanced Settings → Secrets in Streamlit Cloud.

👨‍💻 Author

Srujith Bollam
📧 Email: srujithbollamwork@gmail.com

🔗 GitHub: https://github.com/srujithbollamwork?tab=repositories

🔗 LinkedIn: www.linkedin.com/in/srujith-bollam

📜 License

This project is licensed under the MIT License.

⭐ Contributing

Contributions are welcome!

Fork the repo

Create a new branch (feature/new-feature)

Commit your changes

Open a Pull Request

📌 Notes

Superadmin Role: The email srujithbollamwork@gmail.com is permanently designated as the superadmin.

Other users can only register as user, and may be promoted to admin by the superadmin.
