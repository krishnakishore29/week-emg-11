# Titanic Passenger Explorer

This folder contains the Titanic PostgreSQL and Streamlit lab project.

## What is included

- `Titanic-Dataset.csv` - the 891 passenger records.
- `01_create_database.sql` - creates the `titanic_db` database if it does not exist.
- `02_setup_tables.sql` - creates and fills the staging and passengers tables.
- `app.py` - a 1,000-line Streamlit app with a dashboard, passenger filters, 68 SQL lessons, 43 quiz questions, and a column guide.
- `requirements.txt` - the packages needed to run the app.

The app reads `titanic_project.titanic_staging`, which preserves the original CSV columns. It avoids importing pandas because Windows blocked one of pandas' compiled components on this laptop.

## Start the app

Open a PowerShell terminal in this folder and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

When the browser opens, enter the PostgreSQL password in the left sidebar. The password is used to connect to the local database and is not included in the project files.

The database is already set up in this copy of the project. Do not rerun the SQL setup files unless you are starting with a fresh database.

