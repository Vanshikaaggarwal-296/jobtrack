import html
import re
import sqlite3
from datetime import date
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "jobtrack.db"
STATUSES = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn"]
SKILLS = [
    "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
    "machine learning", "scikit-learn", "data analysis", "data visualization",
    "fastapi", "django", "flask", "streamlit", "git", "docker", "aws",
    "azure", "communication", "leadership", "project management", "javascript",
    "react", "html", "css", "api", "linux", "statistics", "deep learning",
]

st.set_page_config(page_title="JobTrack | Career workspace", page_icon="💼", layout="wide")


def connect():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                location TEXT DEFAULT '',
                job_url TEXT DEFAULT '',
                applied_on TEXT NOT NULL,
                follow_up TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )
        """)


def get_applications():
    with connect() as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            "SELECT * FROM applications ORDER BY applied_on DESC, id DESC"
        ).fetchall()]


def add_application(values):
    with connect() as db:
        db.execute("""
            INSERT INTO applications
            (company, role, status, location, job_url, applied_on, follow_up, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, values)


def update_status(app_id, status):
    with connect() as db:
        db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))


def delete_application(app_id):
    with connect() as db:
        db.execute("DELETE FROM applications WHERE id = ?", (app_id,))


initialize_db()
applications = get_applications()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 85% 0%, #13283a 0%, #0b1220 40%, #090e18 100%); color: #e7eef8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #0b1220; border-right: 1px solid #1d2a3a; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.035em; }
h1 { font-size: 2.2rem !important; }
[data-testid="stMetric"] { background: linear-gradient(145deg,#131f30,#101927); padding: 20px 22px; border: 1px solid #243449; border-radius: 16px; }
[data-testid="stMetricLabel"] { color: #8ea2b9; }
[data-testid="stMetricValue"] { color: #f5f8fc; }
div[data-testid="stForm"], div[data-testid="stExpander"] { background: #101a29; border: 1px solid #233449; border-radius: 14px; padding: 12px; }
div[data-testid="stTabs"] button { color: #9db0c5; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #63d5c2; }
.eyebrow { color: #63d5c2; text-transform: uppercase; letter-spacing: .14em; font-size: .74rem; font-weight: 700; }
.muted { color: #91a3b8; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button { background: #36b9a7; color: #071511; border: 0; border-radius: 9px; font-weight: 700; }
div.stButton > button { border-radius: 9px; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] > div { background-color: #0c1522; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 💼 JobTrack")
    st.caption("YOUR CAREER WORKSPACE")
    st.divider()
    st.markdown("**Keep your search moving.**")
    st.caption("Track applications, follow-ups, and the skills each role asks for.")
    st.divider()
    st.caption("Local database · Your records stay on this computer")

st.markdown('<div class="eyebrow">CAREER SEARCH WORKSPACE</div>', unsafe_allow_html=True)
st.title("Your next opportunity, organized.")
st.markdown('<p class="muted">A clear view of every application and what to do next.</p>', unsafe_allow_html=True)

total = len(applications)
interviews = sum(a["status"] == "Interview" for a in applications)
offers = sum(a["status"] == "Offer" for a in applications)
follow_ups = sum(bool(a["follow_up"]) and a["follow_up"] <= date.today().isoformat() and a["status"] not in ("Rejected", "Withdrawn", "Offer") for a in applications)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Applications", total, help="All roles saved in your tracker")
m2.metric("Interviews", interviews)
m3.metric("Offers", offers)
m4.metric("Follow-ups due", follow_ups)

overview_tab, applications_tab, matcher_tab = st.tabs(["Overview", "Applications", "Resume match"])

with overview_tab:
    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Application pipeline")
        if applications:
            counts = {status: sum(a["status"] == status for a in applications) for status in STATUSES}
            st.bar_chart(counts, color="#36b9a7", height=260)
        else:
            st.info("Your pipeline is empty. Add your first role in the Applications tab.")
    with right:
        st.subheader("Next actions")
        due = [a for a in applications if a["follow_up"] and a["follow_up"] <= date.today().isoformat() and a["status"] not in ("Rejected", "Withdrawn", "Offer")]
        if due:
            for app in due[:5]:
                st.warning(f"**{app['company']}** · {app['role']} — follow up by {app['follow_up']}")
        elif applications:
            st.success("You’re all caught up. Add follow-up dates to keep momentum.")
        else:
            st.caption("Follow-up reminders will show here once you add applications.")
    st.subheader("Recently added")
    if applications:
        recent = applications[:5]
        st.dataframe([{"Company": a["company"], "Role": a["role"], "Status": a["status"], "Applied": a["applied_on"]} for a in recent], use_container_width=True, hide_index=True)
    else:
        st.caption("Your recent applications will appear here.")

with applications_tab:
    st.subheader("Applications")
    with st.expander("＋ Add a job application", expanded=not applications):
        with st.form("add_application", clear_on_submit=True):
            c1, c2 = st.columns(2)
            company = c1.text_input("Company *", placeholder="e.g. Oracle")
            role = c2.text_input("Job title *", placeholder="e.g. Python Developer")
            c3, c4 = st.columns(2)
            status = c3.selectbox("Status", STATUSES)
            location = c4.text_input("Location", placeholder="Remote, Bengaluru…")
            c5, c6 = st.columns(2)
            job_url = c5.text_input("Job posting URL", placeholder="https://…")
            applied_on = c6.date_input("Date applied", value=date.today())
            follow_up = st.date_input("Follow-up date (optional)", value=None)
            notes = st.text_area("Notes", placeholder="Recruiter, interview prep, key details…", height=90)
            save = st.form_submit_button("Save application", type="primary", use_container_width=True)
            if save:
                if not company.strip() or not role.strip():
                    st.error("Company and job title are required.")
                else:
                    add_application((company.strip(), role.strip(), status, location.strip(), job_url.strip(), applied_on.isoformat(), follow_up.isoformat() if follow_up else "", notes.strip()))
                    st.success(f"Saved {role.strip()} at {company.strip()}.")
                    st.rerun()

    if applications:
        f1, f2 = st.columns([1.5, 1])
        search = f1.text_input("Search applications", placeholder="Search company, role, or location…", key="app_search")
        selected_status = f2.multiselect("Filter by status", STATUSES, default=[], placeholder="All statuses")
        filtered = [a for a in applications if (not selected_status or a["status"] in selected_status) and search.lower() in f"{a['company']} {a['role']} {a['location']}".lower()]
        st.caption(f"Showing {len(filtered)} of {total} applications")
        if filtered:
            st.dataframe([{"Company": a["company"], "Role": a["role"], "Status": a["status"], "Location": a["location"], "Applied": a["applied_on"], "Follow-up": a["follow_up"] or "—"} for a in filtered], use_container_width=True, hide_index=True)
            with st.expander("Update status or remove an application"):
                selected_id = st.selectbox("Choose application", [a["id"] for a in filtered], format_func=lambda app_id: next(f"{a['company']} · {a['role']}" for a in filtered if a["id"] == app_id))
                chosen = next(a for a in filtered if a["id"] == selected_id)
                new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(chosen["status"]), key=f"status_{selected_id}")
                b1, b2 = st.columns(2)
                if b1.button("Update status", type="primary", use_container_width=True):
                    update_status(selected_id, new_status)
                    st.rerun()
                if b2.button("Delete application", use_container_width=True):
                    delete_application(selected_id)
                    st.rerun()
        else:
            st.info("No applications match those filters.")
    else:
        st.info("No applications yet. Add your first job above.")

with matcher_tab:
    st.subheader("Resume match")
    st.markdown('<p class="muted">Compare a resume with a job description. Text is analyzed in your browser session and is not sent to an AI service.</p>', unsafe_allow_html=True)
    resume_text = st.text_area("Paste resume text", height=210, placeholder="Paste your resume skills and experience here…")
    job_text = st.text_area("Paste job description", height=210, placeholder="Paste the job requirements here…")
    if st.button("Compare skills", type="primary"):
        if not resume_text.strip() or not job_text.strip():
            st.warning("Paste both your resume and the job description first.")
        else:
            resume_lower, job_lower = resume_text.lower(), job_text.lower()
            required = [skill for skill in SKILLS if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", job_lower)]
            matched = [skill for skill in required if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", resume_lower)]
            missing = [skill for skill in required if skill not in matched]
            score = round(100 * len(matched) / len(required)) if required else 0
            st.session_state["match_result"] = (score, matched, missing, required)
    if "match_result" in st.session_state:
        score, matched, missing, required = st.session_state["match_result"]
        if not required:
            st.info("No skills from the built-in list were found in this job description. Try one with explicit skill names.")
        else:
            st.metric("Skill overlap", f"{score}%", f"{len(matched)} of {len(required)} listed skills")
            st.progress(score / 100)
            good, gaps = st.columns(2)
            with good:
                st.markdown("**Skills found in your resume**")
                st.write(", ".join(matched) if matched else "No matches found yet.")
            with gaps:
                st.markdown("**Skills to highlight or build**")
                st.write(", ".join(missing) if missing else "No listed skill gaps found.")
            st.caption("This is a simple keyword comparison, not an assessment of your qualifications.")

st.divider()
st.caption("JobTrack · A personal job search workspace")
