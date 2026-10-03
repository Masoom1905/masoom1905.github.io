# Northbound Journal — Flask Vlogging Website

A dynamic, database-backed vlogging website built with **Python (Flask)** and
**SQLite**. Content is not hardcoded into the HTML — everything (episodes,
comments, journal posts, view counts, newsletter signups, contact messages)
is stored in a database and rendered on the fly.

## Pages (7)

| Page | Route | What makes it dynamic |
|---|---|---|
| Home | `/` | Pulls the 3 latest episodes, live stats (episode count, total views), and series breakdown straight from the database |
| Episodes | `/videos` | Filter by series and search by keyword via query string, both run as live SQL queries |
| Episode detail | `/video/<id>` | Embeds the video, increments the view counter on every visit, loads and accepts new comments |
| Journal | `/journal` | Lists blog-style posts from the database |
| Journal post | `/journal/<id>` | Single post with related posts pulled dynamically |
| About | `/about` | Stats (episode count, total views, first publish date) computed live from the database |
| Contact | `/contact` | Working form — messages are saved to the database |
| Publish (bonus) | `/upload` | A simple "creator dashboard" — submitting the form inserts a brand-new episode that immediately appears on Home and Episodes |

Plus a newsletter signup form (in the footer band on every page) and a
custom 404 page.

## Tech stack

- **Flask** — routing, templating, form handling
- **SQLite** (via the standard library `sqlite3`) — no separate database server needed
- **Jinja2** — server-side templating (already bundled with Flask)
- Hand-written HTML/CSS (no frontend framework required) — responsive, no external JS dependencies

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The first run automatically creates `vlogs.db` and seeds it with sample
episodes, comments, and journal posts, so the site is fully populated right
away. Delete `vlogs.db` at any time to reset back to the seed data.

## Project structure

```
vlogsite/
├── app.py                  # Flask app: routes, DB setup, seed data
├── requirements.txt
├── vlogs.db                 # created automatically on first run
├── static/
│   └── css/style.css        # all styling — single stylesheet, CSS custom properties
└── templates/
    ├── base.html             # shared header / nav / newsletter / footer
    ├── home.html
    ├── videos.html
    ├── video_detail.html
    ├── journal.html
    ├── journal_post.html
    ├── about.html
    ├── contact.html
    ├── upload.html
    └── 404.html
```

## Making it your own

- **Swap in real video files:** replace the YouTube embed in
  `video_detail.html` with an `<video>` tag pointing at your own hosted files.
- **Add authentication:** the `/upload` route currently has no login check —
  wrap it with `flask-login` before deploying publicly, or it lets any visitor
  publish an episode.
- **Deploy:** for production use a real WSGI server (e.g. `gunicorn app:app`)
  behind Nginx, and move `app.secret_key` into an environment variable.
