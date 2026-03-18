# cs125-project

> Ensure you are running in a venv

1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py runserver`

App will be available at `localhost:8000`

To re-run ingestion and fetch new places from Google Places, delete the `RawDataRepository_*.zip` file and `data/` directory and set the `GOOGLE_API_KEY` environment variable to your google places API key.
