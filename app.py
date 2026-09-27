import re
from datetime import date

import streamlit as st
from supabase import create_client


STATUSES = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn"]
SKILLS = [
    "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
    "machine learning", "scikit-learn", "data analysis", "data visualization",
    "fastapi", "django", "flask", "streamlit", "git", "docker", "aws",
    "azure", "communication", "leadership", "project management", "javascript",
    "react", "html", "css", "api", "linux", "statistics", "deep learning",
]

st.set_page_config(page_title="JobTrack | Career workspace", page_icon="💼", layout="wide")


def make_supabase_client():
    """Create a client with the public key; RLS protects every user's rows."""
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["publishable_key"])


def get_applications(client):
    return (
        client.table("applications")
        .select("id, company, role, status, location, job_url, applied_on, follow_up, notes")
        .order("applied_on", desc=True)
        .execute()
        .data
    )


def add_application(client, values):
    client.table("applications").insert(values).execute()


def update_status(client, app_id, status):
    client.table("applications").update({"status": status}).eq("id", app_id).execute()


def delete_application(client, app_id):
    client.table("applications").delete().eq("id", app_id).execute()


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

try:
    if "jobtrack_supabase_client" not in st.session_state:
        st.session_state.jobtrack_supabase_client = make_supabase_client()
    client = st.session_state.jobtrack_supabase_client
except Exception:
    st.title("💼 JobTrack")
    st.error("Supabase settings were not found. Add the app URL and publishable key to `.streamlit/secrets.toml`.")
    st.stop()

if "jobtrack_user_id" not in st.session_state:
    st.markdown('<div class="eyebrow">YOUR PRIVATE CAREER WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Welcome to JobTrack")
    st.markdown('<p class="muted">Sign in or create an account. Your applications are private to your account.</p>', unsafe_allow_html=True)
    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            sign_in = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if sign_in:
            try:
                response = client.auth.sign_in_with_password({"email": login_email.strip(), "password": login_password})
                if response.user and response.session:
                    st.session_state.jobtrack_user_id = response.user.id
                    st.session_state.jobtrack_user_email = response.user.email or login_email.strip()
                    st.rerun()
                st.error("Sign-in failed. Check your email and password.")
            except Exception:
                st.error("Sign-in failed. Check your email and password, or verify your email first.")

    with sign_up_tab:
        with st.form("sign_up_form"):
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password (at least 8 characters)", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            sign_up = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if sign_up:
            if not signup_email.strip() or "@" not in signup_email:
                st.error("Enter a valid email address.")
            elif len(signup_password) < 8:
                st.error("Your password must be at least 8 characters long.")
            elif signup_password != signup_confirm:
                st.error("The passwords do not match.")
            else:
                try:
                    response = client.auth.sign_up({"email": signup_email.strip(), "password": signup_password})
                    if response.session and response.user:
                        st.session_state.jobtrack_user_id = response.user.id
                        st.session_state.jobtrack_user_email = response.user.email or signup_email.strip()
                        st.rerun()
                    st.success("Your account was created. Check your inbox for the verification link, then sign in.")
                except Exception:
                    st.error("Account creation failed. Check the email address, or try signing in if you already registered.")
    st.caption("Supabase Auth manages your password; JobTrack does not store it.")
    st.stop()

with st.sidebar:
    st.markdown("# 💼 JobTrack")
    st.caption("YOUR CAREER WORKSPACE")
    st.divider()
    st.caption(st.session_state.get("jobtrack_user_email", "Signed in"))
    if st.button("Sign out", use_container_width=True):
        try:
            client.auth.sign_out()
        finally:
            st.session_state.pop("jobtrack_user_id", None)
            st.session_state.pop("jobtrack_user_email", None)
            st.rerun()
    st.divider()
    st.caption("Your applications are protected by Supabase Row Level Security.")

st.markdown('<div class="eyebrow">CAREER SEARCH WORKSPACE</div>', unsafe_allow_html=True)
st.title("Your next opportunity, organized.")
st.markdown('<p class="muted">A clear view of every application and what to do next.</p>', unsafe_allow_html=True)

try:
    applications = get_applications(client)
except Exception:
    st.error("Applications could not be loaded. Check the Supabase table, RLS policies, and app credentials.")
    st.stop()

total = len(applications)
interviews = sum(a["status"] == "Interview" for a in applications)
offers = sum(a["status"] == "Offer" for a in applications)
today = date.today().isoformat()
follow_ups = sum(bool(a["follow_up"]) and a["follow_up"] <= today and a["status"] not in ("Rejected", "Withdrawn", "Offer") for a in applications)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Applications", total)
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
        due = [a for a in applications if a["follow_up"] and a["follow_up"] <= today and a["status"] not in ("Rejected", "Withdrawn", "Offer")]
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
                    try:
                        add_application(client, {
                            "company": company.strip(), "role": role.strip(), "status": status,
                            "location": location.strip(), "job_url": job_url.strip(),
                            "applied_on": applied_on.isoformat(),
                            "follow_up": follow_up.isoformat() if follow_up else None,
                            "notes": notes.strip(),
                        })
                        st.success(f"Saved {role.strip()} at {company.strip()}.")
                        st.rerun()
                    except Exception:
                        st.error("The application could not be saved. Check your sign-in session and Supabase access policies.")

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
                    try:
                        update_status(client, selected_id, new_status)
                        st.rerun()
                    except Exception:
                        st.error("The status could not be updated. Sign in again and try once more.")
                if b2.button("Delete application", use_container_width=True):
                    try:
                        delete_application(client, selected_id)
                        st.rerun()
                    except Exception:
                        st.error("The application could not be deleted. Sign in again and try once more.")
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
