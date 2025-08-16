# DailyNest — Public Daily Activities & Location Tracker

**Brand:** DailyNest  
**Footer:** Developed by Hussain

## Local run
```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## Deploy to Render
1. Create a new **Web Service** from this repo/zip.
2. Environment: **Python**.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   gunicorn -w 2 -k gthread -t 120 app:app
   ```
5. Add env vars:
   - `SECRET_KEY` = (any random string)
   - `DATABASE_URL` = `sqlite:///app.db` (or a PostgreSQL URL if you prefer)

> The app listens on the port Render provides automatically via Gunicorn.

## Features
- Public feed, profiles, login/register
- Create activity (title, description, mood, category)
- Privacy toggle (public/private)
- Location (manual lat/lng or browser geolocation button)
- Clean Tailwind UI
