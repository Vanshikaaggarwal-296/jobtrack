# JobTrack

A personal job-search dashboard built with Python and Streamlit. Track applications, monitor follow-ups, and compare resume skills with job requirements.

## Features

- Dashboard with application, interview, offer, and follow-up counts
- Add applications with company, role, status, dates, and notes
- Search and filter applications
- Update application status or delete an entry
- Compare resume text with a job description using skill keywords
- Save application data locally in SQLite

## Tech stack

Python · Streamlit · SQLite

## Run locally

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
      ```

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start JobTrack:

   ```powershell
   python -m streamlit run app.py
   ```

The app opens in your browser. Application records are stored in `jobtrack.db` in the project folder. The resume matcher uses a simple keyword comparison; it does not assess qualifications or send text to an AI service.