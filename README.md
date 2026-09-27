# JobTrack

A career-search dashboard for tracking job applications, interview progress, and follow-ups. Users create an account, and Supabase Row Level Security keeps each person's applications private to their account.

## Features

- Account sign-up and sign-in
- Private, persistent application records stored in Supabase
- Dashboard metrics and an application pipeline
- Employer response, interview, and offer conversion analytics
- Add, search, filter, update, and delete job applications
- Follow-up reminders
- Resume and job-description keyword matching with skill-gap guidance
- Dark, responsive Streamlit interface

## Tech stack

Python · Streamlit · Supabase Auth · PostgreSQL

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
   ```

4. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

Never commit `secrets.toml` or a Supabase secret/service-role key. The local secrets file is excluded by `.gitignore`.

## Deploy

Deploy this public GitHub repository on [Streamlit Community Cloud](https://share.streamlit.io/), using branch `main` and entrypoint `app.py`. Add the same `[supabase]` settings in the app's Cloud secrets configuration; do not put credentials in the repository.

## Notes

The resume matcher uses a built-in keyword list. Its score is a rough keyword overlap, not a hiring probability or an assessment of qualifications. Resume and job-description text is used in the current session and is not saved as an application record. Conversion rates are calculated from the application statuses each user records.
