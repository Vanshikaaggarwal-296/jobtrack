import re
import json
from datetime import date
from html import escape, unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
from supabase import create_client


STATUSES = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn", "Saved"]
ADZUNA_RESULTS_PER_PAGE = 20
JOB_TITLE_SUGGESTIONS = sorted({
    "Accountant", "Administrative Assistant", "Advocate", "AI Engineer",
    "Android Developer", "Backend Developer", "Business Analyst",
    "Business Development Executive", "Chartered Accountant", "Chef",
    "Civil Engineer", "Cloud Engineer", "Content Writer", "Customer Support Executive",
    "Cybersecurity Analyst", "Data Analyst", "Data Engineer", "Data Scientist",
    "Database Administrator", "Delivery Manager", "DevOps Engineer", "Digital Marketing Executive",
    "Doctor", "Electrical Engineer", "Embedded Systems Engineer", "Finance Analyst",
    "Frontend Developer", "Full Stack Developer", "Graphic Designer", "HR Executive",
    "HR Manager", "Java Developer", "Legal Associate", "Machine Learning Engineer",
    "Marketing Manager", "Mechanical Engineer", "Network Engineer", "Nurse",
    "Operations Analyst", "Product Analyst", "Product Manager", "Project Manager",
    "Python Developer", "QA Engineer", "Recruiter", "Research Analyst",
    "Sales Executive", "Sales Manager", "Software Developer", "Software Engineer",
    "SQL Developer", "Store Manager", "Teacher", "Technical Support Engineer",
    "UI/UX Designer", "Video Editor", "Web Developer",
})
INDIA_CITIES_BY_STATE = {
    "Andhra Pradesh": ["Amaravati", "Anantapur", "Guntur", "Kakinada", "Kurnool", "Nellore", "Rajahmundry", "Tirupati", "Vijayawada", "Visakhapatnam"],
    "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat", "Tawang"],
    "Assam": ["Dibrugarh", "Guwahati", "Jorhat", "Silchar", "Tezpur"],
    "Bihar": ["Bhagalpur", "Darbhanga", "Gaya", "Muzaffarpur", "Patna"],
    "Chhattisgarh": ["Bhilai", "Bilaspur", "Durg", "Korba", "Raipur"],
    "Goa": ["Mapusa", "Margao", "Panaji", "Ponda", "Vasco da Gama"],
    "Gujarat": ["Ahmedabad", "Anand", "Bhavnagar", "Gandhinagar", "Jamnagar", "Junagadh", "Rajkot", "Surat", "Vadodara"],
    "Haryana": ["Ambala", "Faridabad", "Gurugram", "Hisar", "Karnal", "Panipat", "Rohtak", "Sonipat"],
    "Himachal Pradesh": ["Dharamshala", "Kullu", "Mandi", "Shimla", "Solan"],
    "Jharkhand": ["Bokaro", "Dhanbad", "Jamshedpur", "Ranchi"],
    "Karnataka": ["Belagavi", "Bengaluru", "Davanagere", "Hubballi", "Kalaburagi", "Mangaluru", "Mysuru", "Shivamogga", "Tumakuru", "Udupi"],
    "Kerala": ["Alappuzha", "Kannur", "Kochi", "Kollam", "Kozhikode", "Palakkad", "Thiruvananthapuram", "Thrissur"],
    "Madhya Pradesh": ["Bhopal", "Gwalior", "Indore", "Jabalpur", "Sagar", "Ujjain"],
    "Maharashtra": ["Amravati", "Chhatrapati Sambhajinagar", "Kolhapur", "Mumbai", "Nagpur", "Nashik", "Navi Mumbai", "Pune", "Solapur", "Thane"],
    "Manipur": ["Imphal", "Thoubal"],
    "Meghalaya": ["Shillong", "Tura"],
    "Mizoram": ["Aizawl", "Lunglei"],
    "Nagaland": ["Dimapur", "Kohima"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Sambalpur"],
    "Punjab": ["Amritsar", "Bathinda", "Jalandhar", "Ludhiana", "Mohali", "Patiala"],
    "Rajasthan": ["Ajmer", "Bikaner", "Jaipur", "Jodhpur", "Kota", "Udaipur"],
    "Sikkim": ["Gangtok", "Namchi"],
    "Tamil Nadu": ["Coimbatore", "Erode", "Madurai", "Salem", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Chennai"],
    "Telangana": ["Hyderabad", "Karimnagar", "Khammam", "Nizamabad", "Warangal"],
    "Tripura": ["Agartala", "Udaipur"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Bareilly", "Ghaziabad", "Gorakhpur", "Kanpur", "Lucknow", "Mathura", "Meerut", "Noida", "Prayagraj", "Varanasi"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Haldwani", "Rishikesh", "Roorkee"],
    "West Bengal": ["Asansol", "Durgapur", "Howrah", "Kolkata", "Siliguri"],
    "Andaman and Nicobar Islands": ["Port Blair"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Silvassa"],
    "Delhi": ["Delhi", "New Delhi"],
    "Jammu and Kashmir": ["Anantnag", "Jammu", "Srinagar"],
    "Ladakh": ["Leh"],
    "Lakshadweep": ["Kavaratti"],
    "Puducherry": ["Karaikal", "Puducherry"],
}
INDIA_STATES = sorted(INDIA_CITIES_BY_STATE)
ALL_INDIA_CITIES = sorted(
    f"{city}, {state}"
    for state, cities in INDIA_CITIES_BY_STATE.items()
    for city in cities
)
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


def clear_city_when_state_changes():
    st.session_state["adzuna_city_input"] = None


@st.cache_data(ttl=3600, show_spinner=False)
def search_adzuna_jobs(query, location, page, app_id, app_key):
    """Search one page of India's Adzuna listings; cache it for one hour."""
    params = urlencode({
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": ADZUNA_RESULTS_PER_PAGE,
        "sort_by": "date",
        "content-type": "application/json",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}?{params}"
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


def render_metric_card(icon, label, value, detail, tone):
    st.markdown(
        f'<div class="metric-card" style="--tone:{tone}">'
        f'<div class="metric-card-top"><span class="metric-icon">{icon}</span><span class="metric-detail">{detail}</span></div>'
        f'<div class="metric-value">{value}</div><div class="metric-label">{label}</div>'
        '<div class="metric-accent"></div></div>',
        unsafe_allow_html=True,
    )


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp { background-color: #080a18; background-image: radial-gradient(1px 1px at 8% 12%,rgba(220,232,255,.62) 98%,transparent),radial-gradient(1px 1px at 18% 72%,rgba(133,157,255,.55) 98%,transparent),radial-gradient(1px 1px at 34% 28%,rgba(220,232,255,.48) 98%,transparent),radial-gradient(1px 1px at 49% 82%,rgba(119,224,202,.45) 98%,transparent),radial-gradient(1px 1px at 63% 16%,rgba(220,232,255,.55) 98%,transparent),radial-gradient(1px 1px at 77% 64%,rgba(172,150,255,.53) 98%,transparent),radial-gradient(1px 1px at 91% 31%,rgba(220,232,255,.48) 98%,transparent),radial-gradient(ellipse at 77% -12%,rgba(76,48,143,.3),transparent 35%),radial-gradient(ellipse at 8% 38%,rgba(25,94,121,.2),transparent 29%); background-size: 100% 100%; color: #edf3fb; }
[data-testid="stHeader"] { background: rgba(8,13,22,.75); backdrop-filter: blur(18px); }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d1522,#090e17); border-right: 1px solid rgba(145,169,197,.13); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #93a5ba; }
.sidebar-brand { display: flex; align-items: center; gap: .75rem; margin: .3rem 0 1.35rem; padding: .85rem .75rem; border: 1px solid rgba(145,169,197,.14); border-radius: 15px; background: linear-gradient(140deg,rgba(33,62,76,.52),rgba(16,27,41,.58)); }
.sidebar-brand-mark { display: grid; place-items: center; width: 40px; height: 40px; border: 1px solid rgba(109,224,194,.42); border-radius: 13px; color: #7ce5c8; background: rgba(52,169,151,.12); font-family: 'Manrope',sans-serif; font-weight: 800; }
.sidebar-brand strong { display: block; color: #f2f6fb; font-family: 'Manrope',sans-serif; font-size: 1rem; }
.sidebar-brand small { display: block; margin-top: .12rem; color: #8196aa; font-size: .58rem; font-weight: 700; letter-spacing: .13em; }
.section-kicker { margin: .4rem 0 .65rem; color: #8097ad; font-size: .67rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
@keyframes enterUp { from { opacity: 0; transform: translateY(9px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slowOrbit { to { transform: rotate(360deg); } }
@keyframes nebulaPulse { 0%,100% { opacity: .35; transform: scale(.98); } 50% { opacity: .58; transform: scale(1.04); } }
@keyframes tapFlash { 0% { opacity: .8; transform: translate(-50%,-50%) scale(.05); } 100% { opacity: 0; transform: translate(-50%,-50%) scale(1.4); } }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3, h4 { font-family: 'Manrope', sans-serif; letter-spacing: -.04em; color: #f3f7fc; }
h1 { font-size: 2.4rem !important; line-height: 1.12 !important; }
h2 { font-size: 1.48rem !important; }
h3 { font-size: 1.15rem !important; }
div.block-container { max-width: 1480px; padding-top: 2.1rem; padding-bottom: 4rem; }
.eyebrow { display: inline-flex; align-items: center; gap: .5rem; color: #77e0ca; text-transform: uppercase; letter-spacing: .16em; font-size: .7rem; font-weight: 700; }
.muted { color: #9aabc0; }
.hero-panel { position: relative; isolation: isolate; overflow: hidden; display: grid; grid-template-columns: minmax(0,1.5fr) minmax(245px,.7fr); gap: 2rem; align-items: center; margin: .35rem 0 1.7rem; padding: clamp(1.5rem,3vw,2.6rem); border: 1px solid rgba(154,137,255,.24); border-radius: 24px; background: radial-gradient(ellipse at 92% 4%,rgba(102,65,183,.24),transparent 34%),linear-gradient(115deg,rgba(17,30,52,.97),rgba(14,22,42,.96) 57%,rgba(23,29,58,.94)); box-shadow: 0 24px 70px rgba(0,0,0,.26), inset 0 1px rgba(255,255,255,.035); animation: enterUp .55s ease-out both; }
.hero-panel:before { content: ''; position: absolute; z-index: -1; width: 340px; height: 340px; right: 7%; top: -70%; border-radius: 50%; background: rgba(131,96,255,.2); filter: blur(65px); }
.hero-copy h1 { margin: .75rem 0 .65rem; max-width: 760px; font-size: clamp(2.1rem,4vw,3.35rem) !important; }
.hero-copy h1 span { color: #6de0c2; }
.hero-copy p { max-width: 690px; color: #a8b8ca; font-size: 1.02rem; line-height: 1.75; }
.hero-aside { position: relative; overflow: hidden; padding: 1.25rem; min-height: 190px; border: 1px solid rgba(157,185,210,.16); border-radius: 18px; background: radial-gradient(circle at 88% 5%,rgba(135,98,255,.22),transparent 43%),linear-gradient(145deg,rgba(255,255,255,.06),rgba(255,255,255,.015)); }
.hero-aside:before { content: ''; position: absolute; right: -42px; top: 2px; width: 190px; height: 190px; border: 1px solid rgba(161,140,255,.28); border-radius: 50%; box-shadow: 0 0 0 17px rgba(161,140,255,.035),0 0 0 36px rgba(161,140,255,.025); animation: slowOrbit 42s linear infinite; pointer-events: none; }
.hero-aside:after { content: ''; position: absolute; right: 41px; top: 59px; width: 8px; height: 8px; border-radius: 50%; background: #a794ff; box-shadow: 0 0 17px 5px rgba(167,148,255,.65); animation: nebulaPulse 4s ease-in-out infinite; pointer-events: none; }
.hero-aside > * { position: relative; z-index: 1; }
.hero-aside-label { color: #8ca2ba; font-size: .67rem; font-weight: 700; letter-spacing: .15em; }
.hero-orbit { display: flex; align-items: center; gap: .65rem; margin: 1.1rem 0 .9rem; }
.hero-orbit span { display: inline-grid; place-items: center; width: 38px; height: 38px; border: 1px solid rgba(109,224,194,.4); border-radius: 12px; color: #7be3c8; background: rgba(52,169,151,.11); font-weight: 800; }
.hero-orbit i { display: block; width: 24px; height: 1px; background: #38566a; }
.hero-orbit b { color: #e9f2fa; font-size: .86rem; }
.hero-note { color: #91a6ba; font-size: .82rem; line-height: 1.55; }
[data-testid="stMetric"] { position: relative; overflow: hidden; min-height: 118px; padding: 18px 19px; border: 1px solid rgba(153,177,203,.14); border-radius: 17px; background: linear-gradient(150deg,rgba(20,33,49,.98),rgba(12,20,32,.98)); box-shadow: 0 12px 28px rgba(0,0,0,.14); transition: transform .2s ease,border-color .2s ease,box-shadow .2s ease; animation: enterUp .45s ease-out both; }
[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: rgba(109,224,194,.4); box-shadow: 0 18px 32px rgba(0,0,0,.24); }
[data-testid="stMetricLabel"] { color: #9aabc0; font-size: .79rem; font-weight: 600; }
[data-testid="stMetricValue"] { color: #f5f8fc; font-family: 'Manrope',sans-serif; font-size: 1.85rem; font-weight: 800; }
[data-testid="stMetricDelta"] { font-size: .72rem; }
[data-testid="stHorizontalBlock"] { gap: 1rem; }
.metric-card { position: relative; min-height: 145px; overflow: hidden; padding: 1rem 1rem .95rem; border: 1px solid color-mix(in srgb,var(--tone) 27%,rgba(153,177,203,.14)); border-radius: 18px; background: linear-gradient(145deg,color-mix(in srgb,var(--tone) 12%,#121d2d),#0c1420 76%); box-shadow: 0 16px 34px rgba(0,0,0,.18); transition: transform .2s ease,border-color .2s ease,box-shadow .2s ease; animation: enterUp .5s ease-out both; }
.metric-card { background: radial-gradient(circle at 92% 4%,color-mix(in srgb,var(--tone) 17%,transparent),transparent 43%),linear-gradient(145deg,color-mix(in srgb,var(--tone) 12%,#121d2d),#0c1420 76%); }
.metric-card:hover { transform: translateY(-4px); border-color: color-mix(in srgb,var(--tone) 52%,#27364a); box-shadow: 0 21px 38px rgba(0,0,0,.28); }
.metric-card:after { content: ''; position: absolute; width: 110px; height: 110px; right: -47px; top: -48px; border-radius: 50%; background: color-mix(in srgb,var(--tone) 20%,transparent); filter: blur(25px); }
.metric-card-top { display: flex; align-items: center; justify-content: space-between; gap: .4rem; }
.metric-icon { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid color-mix(in srgb,var(--tone) 42%,transparent); border-radius: 10px; color: var(--tone); background: color-mix(in srgb,var(--tone) 10%,transparent); font-size: 1rem; font-weight: 800; }
.metric-detail { color: #8498ad; font-size: .62rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.metric-value { margin-top: .7rem; color: #f4f8fc; font-family: 'Manrope',sans-serif; font-size: 2rem; font-weight: 800; line-height: 1; }
.metric-label { margin-top: .32rem; color: #9eafc2; font-size: .76rem; font-weight: 600; }
.metric-accent { position: absolute; left: 1rem; right: 1rem; bottom: 0; height: 2px; border-radius: 2px 2px 0 0; background: linear-gradient(90deg,var(--tone),transparent); opacity: .65; }
.signal-card { padding: 1.25rem; border: 1px solid rgba(145,169,197,.14); border-radius: 18px; background: linear-gradient(145deg,rgba(17,29,44,.96),rgba(11,18,29,.96)); box-shadow: 0 14px 32px rgba(0,0,0,.16); }
.signal-heading { display: flex; align-items: center; justify-content: space-between; gap: .7rem; margin-bottom: 1.15rem; }
.signal-heading strong { color: #e8f0f8; font-family: 'Manrope',sans-serif; font-size: 1rem; }
.signal-heading span { color: #7fe0c6; font-size: .65rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.pipeline-row { display: grid; grid-template-columns: 100px 1fr 34px; align-items: center; gap: .7rem; margin: .95rem 0; }
.pipeline-name { color: #a7b7c8; font-size: .77rem; }
.pipeline-count { color: #eef5fb; font-size: .78rem; font-weight: 700; text-align: right; }
.pipeline-track { height: 7px; overflow: hidden; border-radius: 999px; background: #202d3d; }
.pipeline-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg,#3fc5ae,#73e2c8); box-shadow: 0 0 14px rgba(82,211,185,.3); }
.mini-badge { display: inline-block; padding: .25rem .55rem; border: 1px solid rgba(119,224,202,.2); border-radius: 999px; color: #84e2cb; background: rgba(52,169,151,.08); font-size: .64rem; font-weight: 700; letter-spacing: .06em; }
.recent-row { display: grid; grid-template-columns: minmax(0,1fr) auto; align-items: center; gap: 1rem; padding: .9rem 0; border-bottom: 1px solid rgba(145,169,197,.11); }
.recent-row:last-child { border-bottom: 0; }
.recent-company { color: #e9f0f7; font-weight: 700; }
.recent-role { margin-top: .18rem; color: #92a5b9; font-size: .79rem; }
.recent-date { color: #8194a8; font-size: .72rem; white-space: nowrap; }
div[data-testid="stForm"], div[data-testid="stExpander"] { border: 1px solid rgba(145,169,197,.15); border-radius: 16px; background: rgba(15,25,39,.82); }
div[data-testid="stExpander"] { padding: .2rem .35rem; }
div[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .45rem; padding: .38rem; border: 1px solid rgba(145,169,197,.13); border-radius: 15px; background: rgba(12,20,31,.82); }
div[data-testid="stTabs"] button { min-height: 42px; padding: .3rem 1rem; border-radius: 11px; color: #9aabc0; font-weight: 600; transition: color .18s ease,background .18s ease; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #dffff5; background: linear-gradient(135deg,rgba(48,157,141,.25),rgba(48,157,141,.08)); }
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(145,169,197,.16) !important; border-radius: 17px !important; background: linear-gradient(145deg,rgba(17,28,43,.88),rgba(12,19,30,.9)); transition: transform .18s ease,border-color .18s ease; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: rgba(109,224,194,.32) !important; transform: translateY(-2px); }
div.stButton > button, div.stFormSubmitButton > button, a[data-testid="stLinkButton"] { min-height: 42px; position: relative; overflow: hidden; cursor: pointer; border-radius: 11px; border: 1px solid rgba(145,169,197,.19); transition: transform .16s ease,filter .16s ease,border-color .16s ease,box-shadow .16s ease; }
div.stButton > button:after, div.stFormSubmitButton > button:after, a[data-testid="stLinkButton"]:after { content: ''; position: absolute; top: 50%; left: 50%; width: 180%; aspect-ratio: 1; border-radius: 50%; background: radial-gradient(circle,rgba(190,179,255,.45),rgba(121,104,255,.12) 36%,transparent 68%); opacity: 0; pointer-events: none; }
div.stButton > button:hover, div.stFormSubmitButton > button:hover, a[data-testid="stLinkButton"]:hover { transform: translateY(-2px); border-color: rgba(137,121,255,.62); filter: brightness(1.12); box-shadow: 0 8px 24px rgba(111,83,232,.2); }
div.stButton > button:active, div.stFormSubmitButton > button:active, a[data-testid="stLinkButton"]:active { transform: scale(.96); filter: brightness(1.2); box-shadow: 0 0 0 4px rgba(121,104,255,.18),0 0 24px rgba(121,104,255,.38); }
div.stButton > button:active:after, div.stFormSubmitButton > button:active:after, a[data-testid="stLinkButton"]:active:after { animation: tapFlash .32s ease-out; }
div.stButton > button:focus-visible, div.stFormSubmitButton > button:focus-visible, a[data-testid="stLinkButton"]:focus-visible { outline: 2px solid #9f8cff; outline-offset: 3px; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background: linear-gradient(120deg,#54d9c4,#8b79ff 52%,#bc80ff); background-size: 200% 100%; color: #090d18; border: 0; font-weight: 800; box-shadow: 0 7px 22px rgba(122,102,255,.22); }
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { background-position: 100% 0; box-shadow: 0 10px 28px rgba(122,102,255,.34); }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] > div { border-color: rgba(145,169,197,.2); border-radius: 10px; background-color: #0b1420; }
[data-baseweb="input"] input:focus, [data-baseweb="textarea"] textarea:focus { border-color: #54cbb4; box-shadow: 0 0 0 1px #54cbb4; }
[data-testid="stDataFrame"] { overflow: hidden; border: 1px solid rgba(145,169,197,.16); border-radius: 14px; }
div[data-testid="stAlert"] { border-radius: 13px; }
.auth-hero { position: relative; overflow: hidden; min-height: 560px; padding: clamp(1.8rem,4vw,3.2rem); border: 1px solid rgba(127,190,190,.2); border-radius: 25px; background: radial-gradient(circle at 88% 15%,rgba(65,198,177,.16),transparent 25%),linear-gradient(145deg,#112536,#0d1625 72%); box-shadow: 0 25px 70px rgba(0,0,0,.24); }
.auth-hero { background: radial-gradient(circle at 86% 10%,rgba(141,100,255,.19),transparent 25%),radial-gradient(circle at 5% 92%,rgba(49,168,189,.12),transparent 30%),linear-gradient(145deg,#11192d,#0b1220 72%); border-color: rgba(154,137,255,.24); }
.auth-hero:after { content: ''; position: absolute; z-index: 0; right: -90px; bottom: -135px; width: 320px; height: 320px; border: 1px solid rgba(155,137,255,.28); border-radius: 50%; background: radial-gradient(circle at 35% 30%,rgba(182,152,255,.28),rgba(86,67,153,.16) 40%,rgba(17,25,45,.04) 72%); box-shadow: inset -20px -28px 50px rgba(5,9,23,.5),0 0 85px rgba(101,80,201,.18); animation: nebulaPulse 9s ease-in-out infinite; pointer-events: none; }
.auth-hero > * { position: relative; z-index: 1; }
.auth-brand { display: flex; align-items: center; gap: .75rem; color: #eaf4f8; font-weight: 800; letter-spacing: .08em; }
.auth-brand-mark { display: grid; place-items: center; width: 42px; height: 42px; border: 1px solid rgba(109,224,194,.45); border-radius: 14px; color: #7ce5c8; background: rgba(52,169,151,.13); font-family: 'Manrope',sans-serif; }
.auth-tag { margin-left: .15rem; padding: .28rem .52rem; border: 1px solid rgba(145,169,197,.2); border-radius: 999px; color: #91a8ba; font-size: .6rem; }
.auth-hero h1 { margin: 3.2rem 0 1rem; font-size: clamp(2.5rem,5vw,4.1rem) !important; }
.auth-hero h1 span { color: #70dec2; }
.auth-hero-copy { max-width: 520px; color: #a5b7c9; font-size: 1rem; line-height: 1.8; }
.auth-points { display: grid; gap: .9rem; margin-top: 2.2rem; color: #dce7f1; font-size: .88rem; }
.auth-points span { display: flex; align-items: center; gap: .7rem; }
.auth-points i { color: #76dec2; font-style: normal; }
.auth-footnote { position: absolute; bottom: 1.6rem; color: #8296aa; font-size: .72rem; }
.auth-panel { padding: 1.35rem 1.05rem; border: 1px solid rgba(145,169,197,.15); border-radius: 20px; background: rgba(14,23,36,.78); }
@media (max-width: 850px) { .hero-panel { grid-template-columns: 1fr; } .hero-aside { min-height: 0; } div.block-container { padding-left: 1rem; padding-right: 1rem; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; scroll-behavior: auto !important; } }
/* JobTrack blue-black-slate theme */
.stApp { background-color: #070b13; background-image: radial-gradient(1px 1px at 8% 12%,rgba(222,235,255,.62) 98%,transparent),radial-gradient(1px 1px at 18% 72%,rgba(133,180,235,.52) 98%,transparent),radial-gradient(1px 1px at 34% 28%,rgba(222,235,255,.48) 98%,transparent),radial-gradient(1px 1px at 49% 82%,rgba(160,190,225,.42) 98%,transparent),radial-gradient(1px 1px at 63% 16%,rgba(222,235,255,.55) 98%,transparent),radial-gradient(1px 1px at 77% 64%,rgba(135,177,230,.48) 98%,transparent),radial-gradient(1px 1px at 91% 31%,rgba(222,235,255,.48) 98%,transparent),radial-gradient(ellipse at 77% -12%,rgba(34,78,139,.32),transparent 35%),radial-gradient(ellipse at 8% 38%,rgba(24,58,96,.22),transparent 29%); color: #edf3fb; }
.eyebrow, .hero-copy h1 span, .auth-hero h1 span { color: #8bbcff; }
.hero-panel { border-color: rgba(104,157,220,.25); background: radial-gradient(ellipse at 92% 4%,rgba(52,99,158,.24),transparent 34%),linear-gradient(115deg,rgba(17,30,48,.97),rgba(12,21,34,.96) 57%,rgba(22,33,50,.94)); }
.hero-panel:before { background: rgba(76,132,196,.22); }
.hero-aside { background: radial-gradient(circle at 88% 5%,rgba(67,120,187,.2),transparent 43%),linear-gradient(145deg,rgba(255,255,255,.06),rgba(255,255,255,.015)); }
.hero-aside:before { border-color: rgba(123,174,230,.28); box-shadow: 0 0 0 17px rgba(123,174,230,.035),0 0 0 36px rgba(123,174,230,.025); }
.hero-aside:after { background: #9ac8f7; box-shadow: 0 0 17px 5px rgba(138,187,241,.6); }
.hero-orbit span, .auth-brand-mark, .sidebar-brand-mark { border-color: rgba(88,146,211,.48); color: #a5cbf4; background: rgba(52,106,169,.14); }
.metric-card:hover, [data-testid="stMetric"]:hover { border-color: rgba(92,153,228,.4); }
.signal-heading span { color: #92bdf0; }
.pipeline-track i { background: linear-gradient(90deg,#4287dc,#8abfff); box-shadow: 0 0 14px rgba(84,143,210,.3); }
.mini-badge { border-color: rgba(112,164,218,.27); color: #a5c8ef; background: rgba(52,106,169,.12); }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: rgba(92,153,228,.34) !important; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #e3efff; background: linear-gradient(135deg,rgba(52,106,169,.28),rgba(52,106,169,.09)); }
div.stButton > button:after, div.stFormSubmitButton > button:after, a[data-testid="stLinkButton"]:after { background: radial-gradient(circle,rgba(190,218,250,.42),rgba(81,145,215,.12) 36%,transparent 68%); }
div.stButton > button:hover, div.stFormSubmitButton > button:hover, a[data-testid="stLinkButton"]:hover { border-color: rgba(92,153,228,.62); box-shadow: 0 8px 24px rgba(53,105,167,.2); }
div.stButton > button:active, div.stFormSubmitButton > button:active, a[data-testid="stLinkButton"]:active { box-shadow: 0 0 0 4px rgba(67,118,188,.18),0 0 24px rgba(67,118,188,.38); }
div.stButton > button:focus-visible, div.stFormSubmitButton > button:focus-visible, a[data-testid="stLinkButton"]:focus-visible { outline-color: #8ab8ed; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background: linear-gradient(120deg,#579cf0,#4a83c4 52%,#88b4ed); box-shadow: 0 7px 22px rgba(67,118,188,.24); }
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { box-shadow: 0 10px 28px rgba(67,118,188,.34); }
[data-baseweb="input"] input:focus, [data-baseweb="textarea"] textarea:focus { border-color: #6ea7e2; box-shadow: 0 0 0 1px #6ea7e2; }
.auth-hero { border-color: rgba(104,157,220,.25); background: radial-gradient(circle at 86% 10%,rgba(67,120,187,.2),transparent 25%),radial-gradient(circle at 5% 92%,rgba(39,83,131,.15),transparent 30%),linear-gradient(145deg,#111b2b,#0b1220 72%); }
.auth-hero:after { border-color: rgba(123,174,230,.28); background: radial-gradient(circle at 35% 30%,rgba(137,184,235,.24),rgba(57,92,138,.16) 40%,rgba(17,25,45,.04) 72%); box-shadow: inset -20px -28px 50px rgba(5,9,23,.5),0 0 85px rgba(56,101,156,.2); }
.auth-points i { color: #96c1f1; }
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap: .25rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .62rem .7rem; border: 1px solid transparent; border-radius: 11px; color: #aab7c7; transition: background .16s ease,border-color .16s ease,color .16s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { border-color: rgba(92,153,228,.28); background: rgba(52,106,169,.12); color: #e8f2ff; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { border-color: rgba(92,153,228,.34); background: linear-gradient(110deg,rgba(52,106,169,.25),rgba(52,106,169,.08)); color: #dcecff; }
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
    auth_left, auth_right = st.columns([1.12, .88], gap="large", vertical_alignment="center")
    with auth_left:
        st.markdown("""
        <section class="auth-hero">
          <div class="auth-brand"><span class="auth-brand-mark">JT</span> JOBTRACK <span class="auth-tag">CAREER WORKSPACE</span></div>
          <div class="eyebrow" style="margin-top:3.3rem">YOUR NEXT CHAPTER STARTS HERE</div>
          <h1>Make your next move<br><span>count.</span></h1>
          <p class="auth-hero-copy">Bring your job search into focus. Find relevant roles, keep every application organized, and know what deserves your attention next.</p>
          <div class="auth-points"><span><i>✦</i> Discover jobs across India</span><span><i>✦</i> Keep your application pipeline clear</span><span><i>✦</i> Spot skills to highlight for each role</span></div>
          <div class="auth-footnote">A more intentional way to move your career forward.</div>
        </section>
        """, unsafe_allow_html=True)
    with auth_right:
        st.markdown('<section class="auth-panel"><div class="eyebrow">WELCOME BACK</div><h2 style="margin:.5rem 0 .35rem">Your workspace awaits.</h2><p class="muted">Sign in or create your private JobTrack account.</p></section>', unsafe_allow_html=True)
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

        with sign_in_tab:
            with st.form("sign_in_form"):
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                sign_in = st.form_submit_button("Sign in to JobTrack", type="primary", use_container_width=True)
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
                sign_up = st.form_submit_button("Create your account", type="primary", use_container_width=True)
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
    st.markdown('<div class="sidebar-brand"><span class="sidebar-brand-mark">JT</span><div><strong>JobTrack</strong><small>CAREER WORKSPACE</small></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">WORKSPACE</div>', unsafe_allow_html=True)
    active_page = st.radio(
        "Workspace navigation",
        ["Overview", "Find jobs", "Applications", "Resume match"],
        format_func=lambda page: {
            "Overview": "⌂   Overview",
            "Find jobs": "⌕   Find jobs",
            "Applications": "▤   Applications",
            "Resume match": "◈   Resume match",
        }[page],
        label_visibility="collapsed",
        key="active_page",
    )
    st.divider()
    st.markdown('<div class="section-kicker">ACCOUNT</div>', unsafe_allow_html=True)
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

if active_page == "Overview":
    st.markdown("""
<section class="hero-panel">
  <div class="hero-copy">
    <div class="eyebrow">CAREER SEARCH · INDIA</div>
    <h1>Your next opportunity,<br><span>in motion.</span></h1>
    <p>One calm, clear workspace to discover roles, keep your applications moving, and make every next step count.</p>
  </div>
  <div class="hero-aside">
    <div class="hero-aside-label">YOUR CAREER CONTROL CENTER</div>
    <div class="hero-orbit"><span>01</span><i></i><span>02</span><i></i><span>03</span></div>
    <div class="hero-orbit"><b>Discover</b><i></i><b>Organize</b><i></i><b>Advance</b></div>
    <div class="hero-note">Small, consistent actions make a focused job search easier to manage.</div>
  </div>
</section>
    """, unsafe_allow_html=True)

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

if active_page == "Overview":
    st.markdown('<div class="section-kicker">YOUR SEARCH · LIVE SNAPSHOT</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    for column, item in zip((m1, m2, m3, m4, m5), (
        ("↗", "Applications", application_count, "IN PIPELINE", "#68a9f4"),
        ("◇", "Saved jobs", saved_jobs, "SHORTLIST", "#88b4ed"),
        ("◉", "Interviews", interviews, "IN PROGRESS", "#acc4e1"),
        ("✦", "Offers", offers, "MILESTONE", "#b7c4d3"),
        ("◷", "Follow-ups due", follow_ups, "NEXT ACTION", "#829ab3"),
    )):
        with column:
            render_metric_card(*item)

    st.markdown('<div class="section-kicker">MOMENTUM & CONVERSION</div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        render_metric_card("↗", "Employer response rate", f"{response_rate:.0%}", "REPLIES", "#68a9f4")
    with a2:
        render_metric_card("◎", "Application → interview", f"{interview_rate:.0%}", "CONVERSION", "#88b4ed")
    with a3:
        render_metric_card("✧", "Interview → offer", f"{offer_conversion:.0%}" if interviews else "—", "MILESTONE", "#b7c4d3")
    st.caption("These rates are based on the statuses you record. They describe your tracked applications, not the whole job market.")
    left, right = st.columns([1.15, 1])
    with left:
        pipeline = [
            ("Saved", saved_jobs),
            ("Applied", sum(a["status"] == "Applied" for a in applications)),
            ("Interview", interviews),
            ("Offer", offers),
            ("Closed", sum(a["status"] in ("Rejected", "Withdrawn") for a in applications)),
        ]
        pipeline_html = ['<div class="signal-card"><div class="signal-heading"><strong>Application pipeline</strong><span>Live overview</span></div>']
        if applications:
            denominator = max(total, 1)
            for stage, count in pipeline:
                width = min(100, round(count / denominator * 100))
                pipeline_html.append(
                    f'<div class="pipeline-row"><span class="pipeline-name">{stage}</span>'
                    f'<div class="pipeline-track"><i style="width:{width}%"></i></div>'
                    f'<span class="pipeline-count">{count}</span></div>'
                )
        else:
            pipeline_html.append('<p class="muted">Your pipeline is ready. Add a role to see progress here.</p>')
        pipeline_html.append('</div>')
        st.markdown("".join(pipeline_html), unsafe_allow_html=True)
    with right:
        due = [a for a in applications if a["follow_up"] and a["follow_up"] <= today and a["status"] not in ("Rejected", "Withdrawn", "Offer", "Saved")]
        action_html = ['<div class="signal-card"><div class="signal-heading"><strong>Next actions</strong><span>Keep moving</span></div>']
        if due:
            for app in due[:5]:
                company_html = escape(clean_job_text(app["company"]))
                role_html = escape(clean_job_text(app["role"]))
                action_html.append(f'<div class="recent-row"><div><div class="recent-company">{company_html}</div><div class="recent-role">{role_html}</div></div><span class="mini-badge">DUE {app["follow_up"]}</span></div>')
        elif applications:
            action_html.append('<p class="muted">You’re all caught up. Add follow-up dates to keep your momentum visible.</p>')
        else:
            action_html.append('<p class="muted">Your reminders will appear here when you add applications.</p>')
        action_html.append('</div>')
        st.markdown("".join(action_html), unsafe_allow_html=True)
    st.markdown('<div class="section-kicker" style="margin-top:1.8rem">YOUR LATEST MOVES</div>', unsafe_allow_html=True)
    if applications:
        for app in applications[:5]:
            with st.container(border=True):
                row_left, row_right = st.columns([3, 1])
                company_html = escape(clean_job_text(app["company"]))
                role_html = escape(clean_job_text(app["role"]))
                status_html = escape(app["status"].upper())
                row_left.markdown(f'**{company_html}**<div class="recent-role">{role_html}</div>', unsafe_allow_html=True)
                row_right.markdown(f'<div style="text-align:right"><span class="mini-badge">{status_html}</span><div class="recent-date" style="margin-top:.45rem">{app["applied_on"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="signal-card"><strong>Start your pipeline</strong><p class="muted">Save a promising role or add an application. JobTrack will keep your next steps in view.</p></div>', unsafe_allow_html=True)

elif active_page == "Find jobs":
    st.subheader("Search jobs in India")
    st.markdown('<p class="muted">Search Adzuna listings across India or enter a city. Browse matching results page by page, save roles, then mark them Applied when you apply.</p>', unsafe_allow_html=True)
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
        q1, q2, q3 = st.columns([1.3, 1, 1.2])
        job_query = q1.selectbox(
            "Job title or field",
            JOB_TITLE_SUGGESTIONS,
            index=None,
            placeholder="Choose a role or type any field",
            accept_new_options=True,
            filter_mode="contains",
            help="Choose a suggestion or type any role, industry, or keyword.",
            key="adzuna_job_query_input",
        )
        selected_state = q2.selectbox(
            "State / union territory",
            ["All India", *INDIA_STATES],
            index=0,
            accept_new_options=True,
            filter_mode="contains",
            help="Choose a state to see its city suggestions, or leave All India selected.",
            key="adzuna_state_input",
            on_change=clear_city_when_state_changes,
        )
        city_options = (
            ALL_INDIA_CITIES
            if selected_state == "All India"
            else INDIA_CITIES_BY_STATE.get(selected_state, [])
        )
        selected_city = q3.selectbox(
            "City / locality (optional)",
            city_options,
            index=None,
            placeholder="Choose a city or type one",
            accept_new_options=True,
            filter_mode="contains",
            help="Pick a city from the list or type any city/locality. All India + blank city searches nationwide.",
            key="adzuna_city_input",
        )
        job_location = ""
        if selected_city:
            if selected_state == "All India" and selected_city in ALL_INDIA_CITIES:
                job_location = selected_city
            elif selected_state != "All India" and not selected_city.lower().endswith(f", {selected_state.lower()}"):
                job_location = f"{selected_city}, {selected_state}"
            else:
                job_location = selected_city
        elif selected_state != "All India":
            job_location = selected_state
        search_jobs = st.button("Search jobs", type="primary", use_container_width=True)

        if search_jobs:
            if not job_query or not job_query.strip():
                    st.warning("Enter a job title or keyword first.")
            else:
                try:
                    with st.spinner("Searching current listings…"):
                        result = search_adzuna_jobs(job_query.strip(), job_location.strip(), 1, adzuna_app_id, adzuna_app_key)
                    st.session_state["adzuna_search_results"] = result.get("results", [])
                    st.session_state["adzuna_search_count"] = int(result.get("count", 0) or 0)
                    st.session_state["adzuna_search_query"] = job_query.strip()
                    st.session_state["adzuna_search_location"] = job_location.strip()
                    st.session_state["adzuna_search_page"] = 1
                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("The job search could not load. Check the Adzuna API ID and key in app secrets, then try again.")

        if "adzuna_search_results" in st.session_state:
            job_results = st.session_state["adzuna_search_results"]
            result_location = st.session_state.get("adzuna_search_location", "") or "Across India"
            result_count = int(st.session_state.get("adzuna_search_count", len(job_results)) or 0)
            current_page = int(st.session_state.get("adzuna_search_page", 1))
            total_pages = max(1, (result_count + ADZUNA_RESULTS_PER_PAGE - 1) // ADZUNA_RESULTS_PER_PAGE)
            first_result = ((current_page - 1) * ADZUNA_RESULTS_PER_PAGE + 1) if result_count else 0
            last_result = min(current_page * ADZUNA_RESULTS_PER_PAGE, result_count)
            st.caption(f"{result_count:,} matching listings · showing {first_result}–{last_result} · page {current_page} of {total_pages} · results cached for one hour")
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
                            btn2.button("Already saved", key=f"saved_job_{current_page}_{index}", disabled=True)
                        elif btn2.button("＋ Save to JobTrack", key=f"save_job_{current_page}_{index}", type="primary"):
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

            if result_count > ADZUNA_RESULTS_PER_PAGE:
                previous_col, page_col, next_col = st.columns([1, 2, 1])
                previous_clicked = previous_col.button("← Previous", disabled=current_page <= 1, use_container_width=True)
                page_col.markdown(f"<div style='text-align:center;padding:.45rem'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
                next_clicked = next_col.button("More jobs →", disabled=current_page >= total_pages, use_container_width=True)
                if previous_clicked or next_clicked:
                    target_page = current_page - 1 if previous_clicked else current_page + 1
                    try:
                        with st.spinner(f"Loading page {target_page}…"):
                            result = search_adzuna_jobs(
                                st.session_state["adzuna_search_query"],
                                st.session_state.get("adzuna_search_location", ""),
                                target_page,
                                adzuna_app_id,
                                adzuna_app_key,
                            )
                        st.session_state["adzuna_search_results"] = result.get("results", [])
                        st.session_state["adzuna_search_count"] = int(result.get("count", 0) or 0)
                        st.session_state["adzuna_search_page"] = target_page
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Could not load that results page. Please try again in a moment.")
            st.caption("Listings and salary details are provided by The Adzuna API. Always check the original posting before applying.")

elif active_page == "Applications":
    st.subheader("Applications")
    with st.expander("＋ Add a job application", expanded=not applications):
        with st.form("add_application", clear_on_submit=True):
            c1, c2 = st.columns(2)
            company = c1.text_input("Company *", placeholder="e.g. Oracle")
            role = c2.selectbox(
                "Job title *",
                JOB_TITLE_SUGGESTIONS,
                index=None,
                placeholder="Choose a role or type any job title",
                accept_new_options=True,
                filter_mode="contains",
                help="Choose a suggestion or type a title from any career field.",
            )
            c3, c4 = st.columns(2)
            status = c3.selectbox("Status", STATUSES)
            location = c4.selectbox(
                "Location",
                ["Remote", *INDIA_STATES, *ALL_INDIA_CITIES],
                index=None,
                placeholder="Choose or type a city/state",
                accept_new_options=True,
                filter_mode="contains",
                help="Choose a suggested Indian city/state or type any location.",
            )
            c5, c6 = st.columns(2)
            job_url = c5.text_input("Job posting URL", placeholder="https://…")
            date_label = "Date saved" if status == "Saved" else "Date applied"
            applied_on = c6.date_input(date_label, value=date.today())
            follow_up = st.date_input("Follow-up date (optional)", value=None)
            notes = st.text_area("Notes", placeholder="Recruiter, interview prep, key details…", height=90)
            save = st.form_submit_button("Save application", type="primary", use_container_width=True)
            if save:
                role_value = (role or "").strip()
                location_value = (location or "").strip()
                if not company.strip() or not role_value:
                    st.error("Company and job title are required.")
                else:
                    try:
                        add_application(client, {
                            "company": company.strip(), "role": role_value, "status": status,
                            "location": location_value, "job_url": job_url.strip(),
                            "applied_on": applied_on.isoformat(),
                            "follow_up": follow_up.isoformat() if follow_up else None,
                            "notes": notes.strip(),
                        })
                        st.success(f"Saved {role_value} at {company.strip()}.")
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

elif active_page == "Resume match":
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
