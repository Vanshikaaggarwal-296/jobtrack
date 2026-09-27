# JobTrack

A career-search dashboard for tracking job applications, interview progress, and follow-ups. Users create an account, and Supabase Row Level Security keeps each person's applications private to their account.

## Features

- Account sign-up and sign-in
- Private, persistent application records stored in Supabase
- Dashboard metrics and an application pipeline
- Employer response, interview, and offer conversion analytics
- Search Adzuna job listings across India, or narrow results to a city/location
- Browse matching listings page by page and save chosen roles to the tracker
- Save a listing to your private tracker, then change it to Applied when you apply
- Add, search, filter, update, and delete job applications
- Follow-up reminders
- Resume and job-description keyword matching with skill-gap guidance
- Dark, responsive Streamlit interface

## Tech stack

Python · Streamlit · Supabase Auth · PostgreSQL · Adzuna API

## Run locally

1. Clone the repository and open a terminal in the project folder.
2. Create a virtual environment and install packages:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` with your Supabase project settings:

   ```toml
   [supabase]
   url = "https://YOUR-PROJECT-REF.supabase.co"
   publishable_key = "YOUR-SUPABASE-PUBLISHABLE-KEY"

   [adzuna]
   app_id = "YOUR-ADZUNA-APP-ID"
   app_key = "YOUR-ADZUNA-APP-KEY"
   ```

   Get the Adzuna app ID and key from [developer.adzuna.com](https://developer.adzuna.com/signup). Keep them in secrets; never commit them.

4. In Supabase SQL Editor, run [`supabase/migrations/20260927_allow_saved_status.sql`](supabase/migrations/20260927_allow_saved_status.sql) once so the existing applications table accepts the `Saved` status.

5. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

Never commit `secrets.toml` or a Supabase secret/service-role key. The local secrets file is excluded by `.gitignore`.

## Deploy

Deploy this public GitHub repository on [Streamlit Community Cloud](https://share.streamlit.io/), using branch `main` and entrypoint `app.py`. Add both the `[supabase]` and `[adzuna]` settings in the app's Cloud secrets configuration; do not put credentials in the repository.

## Notes

The resume matcher uses a built-in keyword list. Its score is a rough keyword overlap, not a hiring probability or an assessment of qualifications. Resume and job-description text is used in the current session and is not saved as an application record. Conversion rates are calculated from the application statuses each user records.

Job search is powered by the [Adzuna API](https://developer.adzuna.com/overview). Listings are cached for one hour, credited to Adzuna, and link to the source posting. Check the original posting for current details before applying. Each user's saved jobs and applications remain private to that user's Supabase account.
