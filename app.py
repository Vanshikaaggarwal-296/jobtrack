import re
import json
from datetime import date
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
from supabase import create_client


STATUSES = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn", "Saved"]
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


@st.cache_data(ttl=3600, show_spinner=False)
def search_adzuna_jobs(query, location, app_id, app_key):
    """Search India's Adzuna listings. Cache results for one hour to respect API limits."""
    params = urlencode({
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": 20,
        "sort_by": "date",
        "content-type": "application/json",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?{params}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "JobTrack/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"The job search provider returned error {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError("Job search is temporarily unavailable. Check your internet connection and try again.") from exc


def clean_job_text(value):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def render_adzuna_credit():
    st.markdown(
        '<div style="display:flex;align-items:center;gap:6px;min-height:23px;margin-top:8px;">'
        '<a href="https://www.adzuna.in/" target="_blank" rel="noopener noreferrer">Jobs</a>'
        '<span>by</span>'
        '<a href="https://www.adzuna.in/" target="_blank" rel="noopener noreferrer">'
        '<img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Adzuna_Logo.png" '
        'alt="Adzuna" style="width:90px;height:auto;vertical-align:middle;">'
        '</a></div>',
        unsafe_allow_html=True,
    )


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
saved_jobs = sum(a["status"] == "Saved" for a in applications)
application_count = total - saved_jobs
interviews = sum(a["status"] == "Interview" for a in applications)
offers = sum(a["status"] == "Offer" for a in applications)
submitted_applications = [a for a in applications if a["status"] not in ("Saved", "Withdrawn")]
responses = sum(a["status"] in ("Interview", "Offer", "Rejected") for a in submitted_applications)
response_rate = responses / len(submitted_applications) if submitted_applications else 0
interview_rate = interviews / len(submitted_applications) if submitted_applications else 0
offer_conversion = offers / interviews if interviews else 0
today = date.today().isoformat()
follow_ups = sum(bool(a["follow_up"]) and a["follow_up"] <= today and a["status"] not in ("Rejected", "Withdrawn", "Offer", "Saved") for a in applications)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Applications", application_count)
m2.metric("Saved jobs", saved_jobs)
m3.metric("Interviews", interviews)
m4.metric("Offers", offers)
m5.metric("Follow-ups due", follow_ups)

overview_tab, job_search_tab, applications_tab, matcher_tab = st.tabs(["Overview", "Find jobs", "Applications", "Resume match"])

with overview_tab:
    st.subheader("Job search performance")
    a1, a2, a3 = st.columns(3)
    a1.metric("Employer response rate", f"{response_rate:.0%}", help="Applications with an interview, offer, or rejection response; withdrawn roles are excluded.")
    a2.metric("Application → interview", f"{interview_rate:.0%}", help="Interviews divided by active applications.")
    a3.metric("Interview → offer", f"{offer_conversion:.0%}" if interviews else "—", help="Offers divided by interviews. This appears once you have an interview.")
    st.caption("These rates are based on the statuses you record. They describe your tracked applications, not the whole job market.")
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
        due = [a for a in applications if a["follow_up"] and a["follow_up"] <= today and a["status"] not in ("Rejected", "Withdrawn", "Offer", "Saved")]
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
        st.dataframe([{"Company": a["company"], "Role": a["role"], "Status": a["status"], "Recorded": a["applied_on"]} for a in recent], use_container_width=True, hide_index=True)
    else:
        st.caption("Your recent applications will appear here.")

with job_search_tab:
    st.subheader("Search jobs in India")
    st.markdown('<p class="muted">Search current listings, save interesting roles, then update them to Applied when you submit an application.</p>', unsafe_allow_html=True)
    adzuna_settings = st.secrets.get("adzuna", {})
    adzuna_app_id = str(adzuna_settings.get("app_id", "")).strip()
    adzuna_app_key = str(adzuna_settings.get("app_key", "")).strip()

    if not adzuna_app_id or not adzuna_app_key:
        st.info("Job search needs the app owner's Adzuna API credentials. App users do not need an Adzuna account.")
        st.markdown("1. Create a developer account at [developer.adzuna.com](https://developer.adzuna.com/signup) and copy the **app ID** and **app key**.\n2. Add them to the app's secrets as `[adzuna]`, `app_id`, and `app_key`. Keep these keys private.")
        with st.expander("Secrets format"):
            st.code('[adzuna]\napp_id = "YOUR_APP_ID"\napp_key = "YOUR_APP_KEY"', language="toml")
        st.caption("For local use, put this under your existing `[supabase]` settings in `.streamlit/secrets.toml`. For the live app, add it under Settings → Secrets in Streamlit Community Cloud.")
    else:
        with st.form("job_search_form"):
            q1, q2 = st.columns([1.4, 1])
            job_query = q1.text_input("Job title or keywords", placeholder="e.g. Python developer")
            job_location = q2.text_input("City or state", placeholder="e.g. Bengaluru, India")
            search_jobs = st.form_submit_button("Search jobs", type="primary", use_container_width=True)

        if search_jobs:
            if not job_query.strip():
                st.warning("Enter a job title or keyword first.")
            else:
                try:
                    with st.spinner("Searching current listings…"):
                        result = search_adzuna_jobs(job_query.strip(), job_location.strip(), adzuna_app_id, adzuna_app_key)
                    st.session_state["adzuna_search_results"] = result.get("results", [])
                    st.session_state["adzuna_search_count"] = int(result.get("count", 0) or 0)
                    st.session_state["adzuna_search_query"] = job_query.strip()
                    st.session_state["adzuna_search_location"] = job_location.strip()
                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("The job search could not load. Check the Adzuna API ID and key in app secrets, then try again.")

        if "adzuna_search_results" in st.session_state:
            job_results = st.session_state["adzuna_search_results"]
            result_location = st.session_state.get("adzuna_search_location", "") or "India"
            st.caption(f"{int(st.session_state.get('adzuna_search_count', len(job_results)) or 0):,} listings found · showing up to {len(job_results)} · cached for one hour")
            if not job_results:
                st.info("No matching jobs found. Try a broader title or a different city.")
            else:
                saved_urls = {a.get("job_url", "") for a in applications if a.get("job_url")}
                for index, job in enumerate(job_results):
                    company_name = clean_job_text((job.get("company") or {}).get("display_name") or "Company not listed")
                    role_name = clean_job_text(job.get("title") or "Job title not listed")
                    location_name = clean_job_text((job.get("location") or {}).get("display_name") or result_location)
                    job_url = job.get("redirect_url", "")
                    description = clean_job_text(job.get("description", ""))
                    salary_min = job.get("salary_min")
                    salary_max = job.get("salary_max")
                    salary = "Salary not listed"
                    if salary_min and salary_max:
                        salary = f"Salary: ₹{salary_min:,.0f}–₹{salary_max:,.0f}"
                    elif salary_min:
                        salary = f"Salary from ₹{salary_min:,.0f}"
                    elif salary_max:
                        salary = f"Salary up to ₹{salary_max:,.0f}"
                    job_type = job.get("contract_time") or job.get("contract_type") or ""
                    created = (job.get("created") or "")[:10]

                    with st.container(border=True):
                        st.subheader(role_name)
                        st.write(f"{company_name} · {location_name}")
                        details = [part for part in (job_type.replace("_", " ").title(), salary, f"Posted {created}" if created else "") if part]
                        st.caption(" · ".join(details))
                        if description:
                            st.write(description[:520] + ("…" if len(description) > 520 else ""))
                        btn1, btn2 = st.columns([1, 5])
                        if job_url:
                            btn1.link_button("View job", job_url, use_container_width=True)
                        if job_url in saved_urls:
                            btn2.button("Already saved", key=f"saved_job_{index}", disabled=True)
                        elif btn2.button("＋ Save to JobTrack", key=f"save_job_{index}", type="primary"):
                            try:
                                add_application(client, {
                                    "company": company_name,
                                    "role": role_name,
                                    "status": "Saved",
                                    "location": location_name,
                                    "job_url": job_url,
                                    "applied_on": today,
                                    "follow_up": None,
                                    "notes": f"Saved from Adzuna job search on {today}. Not yet applied.",
                                })
                                st.success(f"Saved {role_name} at {company_name} to your Applications tab.")
                                st.rerun()
                            except Exception:
                                st.error("Could not save this listing. Check that your Supabase applications table permits the 'Saved' status.")
                        render_adzuna_credit()
            st.caption("Listings and salary details are provided by The Adzuna API. Always check the original posting before applying.")

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
            date_label = "Date saved" if status == "Saved" else "Date applied"
            applied_on = c6.date_input(date_label, value=date.today())
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
            st.dataframe([{"Company": a["company"], "Role": a["role"], "Status": a["status"], "Location": a["location"], "Recorded": a["applied_on"], "Follow-up": a["follow_up"] or "—"} for a in filtered], use_container_width=True, hide_index=True)
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
    st.markdown('<p class="muted">Compare your resume with a job description, see matching skills, and identify gaps. Text is analyzed for this session and is not sent to an AI service.</p>', unsafe_allow_html=True)
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
            st.metric("Keyword match", f"{score}%", f"{len(matched)} of {len(required)} listed skills")
            st.progress(score / 100)
            good, gaps = st.columns(2)
            with good:
                st.markdown("**Skills found in your resume**")
                st.write(", ".join(matched) if matched else "No matches found yet.")
            with gaps:
                st.markdown("**Skills to highlight or build**")
                st.write(", ".join(missing) if missing else "No listed skill gaps found.")
            st.markdown("**Suggested next step**")
            if score >= 70:
                st.info("Many listed skills appear in your resume. Tailor your examples to the role and consider prioritizing this application.")
            elif score >= 40:
                st.info("There is some skill overlap. Highlight your strongest matching experience and review the gaps before applying.")
            else:
                st.info("Few listed skills were found. Review the full role requirements and consider transferable experience before deciding.")
            st.caption("This keyword match is a rough guide, not a hiring probability or an assessment of your qualifications.")

st.divider()
st.caption("JobTrack · A personal job search workspace")
