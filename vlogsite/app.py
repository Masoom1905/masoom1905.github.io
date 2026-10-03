"""
Northbound Journal — a dynamic vlogging website built with Flask + SQLite.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import os
import sqlite3
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, g, abort
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "vlogs.db")

app = Flask(__name__)
app.secret_key = "northbound-dev-secret-key"  # change this in production


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed them with starter content, only if empty."""
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT,
            description TEXT NOT NULL,
            youtube_id TEXT NOT NULL,
            thumbnail TEXT,
            duration TEXT,
            views INTEGER DEFAULT 0,
            published_on TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            excerpt TEXT NOT NULL,
            body TEXT NOT NULL,
            published_on TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    db.commit()

    count = db.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    if count == 0:
        seed_videos = [
            (
                "Sunrise Over the Kalalau Trail",
                "Hiking",
                "Kauai, Hawaii",
                "Eleven miles along the Napali coast, starting before dawn so we "
                "reach the overlook when the light turns the cliffs orange. Pack "
                "list, water strategy, and the moment the trail almost beat us.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
                "18:42",
                48213,
                "2026-08-02",
            ),
            (
                "Cooking With Only a Camp Stove",
                "Food",
                "Isle of Skye, Scotland",
                "One burner, one pan, and whatever the last village shop had left. "
                "A three-day experiment in cooking well with almost nothing.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80",
                "12:05",
                31890,
                "2026-07-19",
            ),
            (
                "Sleeping in a Van Through Winter",
                "Van Life",
                "Banff, Canada",
                "What actually keeps you warm at minus fifteen, why insulation "
                "matters more than heaters, and the three mistakes that nearly "
                "ended the trip early.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800&q=80",
                "22:17",
                67540,
                "2026-06-28",
            ),
            (
                "Freediving the Blue Holes",
                "Diving",
                "Dahab, Egypt",
                "Three weeks learning to hold a breath longer than felt possible, "
                "taught by people who make it look like nothing.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80",
                "15:30",
                52102,
                "2026-06-05",
            ),
            (
                "A Week on the Trans-Siberian",
                "Trains",
                "Irkutsk, Russia",
                "Six days, four strangers turned friends, and a window that never "
                "stopped moving. Notes on the slowest way to cross a continent.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=800&q=80",
                "26:48",
                39877,
                "2026-05-14",
            ),
            (
                "Packing List: Four Seasons, One Bag",
                "Gear",
                "Home Base",
                "Everything that lives in the 40-liter pack year-round, what got "
                "cut this season, and the two items worth the extra weight.",
                "dQw4w9WgXcQ",
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80",
                "9:52",
                28460,
                "2026-04-30",
            ),
        ]
        db.executemany(
            """INSERT INTO videos
               (title, category, location, description, youtube_id, thumbnail,
                duration, views, published_on)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            seed_videos,
        )

        seed_comments = [
            (1, "Maya R.", "The 4am shot of the ridge line is unreal. What lens?"),
            (1, "Theo K.", "Did this after watching your video, hardest and best hike I've done."),
            (3, "Jo Ann", "The insulation breakdown alone saved me a very cold winter."),
        ]
        db.executemany(
            """INSERT INTO comments (video_id, name, body, created_at)
               VALUES (?, ?, ?, ?)""",
            [(v, n, b, "2026-08-03") for v, n, b in seed_comments],
        )

        seed_posts = [
            (
                "Why I Stopped Planning Routes in Advance",
                "Three years of itineraries taught me the best days were always "
                "the ones that weren't on the schedule.",
                "Three years ago every trip had a spreadsheet. Every day had a "
                "destination, a backup destination, and a time to leave for both. "
                "It worked, in the sense that nothing went wrong. It also meant "
                "I was never anywhere I hadn't already decided to be.\n\n"
                "The shift happened in Portugal, on a day I'd planned to drive "
                "north and instead stayed in a fishing town because someone at "
                "breakfast mentioned a boat leaving at noon. That afternoon is "
                "still the one people ask about most. Nothing about it was on "
                "any list.\n\n"
                "I still plan the bones of a trip - how to get in, how to get "
                "out, roughly how long I have. But the days in between are open "
                "now, and almost everything worth filming has come from that "
                "openness rather than in spite of it.",
                "2026-08-10",
            ),
            (
                "The Gear I Regret Buying",
                "Not a haul video. A short list of things that looked essential "
                "in the store and useless on the trail.",
                "Every piece of gear on this list passed a review, a "
                "recommendation, or both before I bought it. All six still "
                "failed the only test that matters, which is whether I reached "
                "for it on trip four.\n\n"
                "A collapsible sink took up a third of a dry bag and got used "
                "once. A satellite messenger with a subscription I forgot to "
                "cancel. A jacket rated for conditions I don't actually film in. "
                "The pattern, in hindsight, is that I bought for the trip I "
                "imagined rather than the one I usually take.",
                "2026-07-22",
            ),
            (
                "Editing on the Road: A Two-Laptop Workflow",
                "How footage gets from a memory card in a tent to a published "
                "video, without a studio anywhere in the chain.",
                "The workflow is duller than people expect. Footage gets backed "
                "up to two drives the same night it's shot, non-negotiably, "
                "before anything else happens. A rough cut happens on travel "
                "days, in transit, on a laptop that's deliberately not the "
                "newest or fastest one I own, because it needs to survive being "
                "dropped.\n\n"
                "Color and sound only happen once I'm somewhere with a real "
                "desk, usually every few weeks. Which means what you see is "
                "often shot a month before it's published. I used to think that "
                "delay was a problem. Now it's the only reason the edits are "
                "any good.",
                "2026-06-30",
            ),
        ]
        db.executemany(
            """INSERT INTO posts (title, excerpt, body, published_on)
               VALUES (?, ?, ?, ?)""",
            seed_posts,
        )

        db.commit()
    db.close()


# --------------------------------------------------------------------------
# Template helpers
# --------------------------------------------------------------------------

@app.context_processor
def inject_globals():
    db = get_db()
    total_videos = db.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    return {
        "site_name": "Northbound Journal",
        "current_year": datetime.now().year,
        "nav_video_count": total_videos,
    }


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.route("/")
def home():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM videos ORDER BY published_on DESC LIMIT 3"
    ).fetchall()
    latest_post = db.execute(
        "SELECT * FROM posts ORDER BY published_on DESC LIMIT 1"
    ).fetchone()
    stats = db.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(views),0) AS total_views FROM videos"
    ).fetchone()
    categories = db.execute(
        "SELECT category, COUNT(*) AS n FROM videos GROUP BY category ORDER BY n DESC"
    ).fetchall()
    return render_template(
        "home.html",
        featured=featured,
        latest_post=latest_post,
        stats=stats,
        categories=categories,
    )


@app.route("/videos")
def videos():
    db = get_db()
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM videos WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]
    query += " ORDER BY published_on DESC"

    video_list = db.execute(query, params).fetchall()
    categories = db.execute(
        "SELECT DISTINCT category FROM videos ORDER BY category"
    ).fetchall()

    return render_template(
        "videos.html",
        videos=video_list,
        categories=categories,
        active_category=category,
        search=search,
    )


@app.route("/video/<int:video_id>")
def video_detail(video_id):
    db = get_db()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video is None:
        abort(404)

    # increment the view count each time the page loads
    db.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))
    db.commit()
    video = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()

    comments = db.execute(
        "SELECT * FROM comments WHERE video_id = ? ORDER BY created_at DESC",
        (video_id,),
    ).fetchall()
    more = db.execute(
        "SELECT * FROM videos WHERE category = ? AND id != ? LIMIT 3",
        (video["category"], video_id),
    ).fetchall()

    return render_template(
        "video_detail.html", video=video, comments=comments, more=more
    )


@app.route("/video/<int:video_id>/comment", methods=["POST"])
def add_comment(video_id):
    db = get_db()
    video = db.execute("SELECT id FROM videos WHERE id = ?", (video_id,)).fetchone()
    if video is None:
        abort(404)

    name = request.form.get("name", "").strip()
    body = request.form.get("body", "").strip()

    if not name or not body:
        flash("Add a name and a comment before posting.", "error")
    else:
        db.execute(
            "INSERT INTO comments (video_id, name, body, created_at) VALUES (?, ?, ?, ?)",
            (video_id, name, body, datetime.now().strftime("%Y-%m-%d")),
        )
        db.commit()
        flash("Comment posted.", "success")

    return redirect(url_for("video_detail", video_id=video_id) + "#comments")


@app.route("/journal")
def journal():
    db = get_db()
    posts = db.execute("SELECT * FROM posts ORDER BY published_on DESC").fetchall()
    return render_template("journal.html", posts=posts)


@app.route("/journal/<int:post_id>")
def journal_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    others = db.execute(
        "SELECT * FROM posts WHERE id != ? ORDER BY published_on DESC LIMIT 2",
        (post_id,),
    ).fetchall()
    return render_template("journal_post.html", post=post, others=others)


@app.route("/about")
def about():
    db = get_db()
    stats = db.execute(
        """SELECT COUNT(*) AS video_count,
                  COALESCE(SUM(views),0) AS total_views,
                  MIN(published_on) AS first_published
           FROM videos"""
    ).fetchone()
    countries = db.execute(
        "SELECT DISTINCT location FROM videos WHERE location IS NOT NULL"
    ).fetchall()
    return render_template("about.html", stats=stats, countries=countries)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not name or not email or not body:
            flash("Name, email, and message are required.", "error")
        else:
            db = get_db()
            db.execute(
                """INSERT INTO messages (name, email, subject, body, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, email, subject, body, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            db.commit()
            flash("Message sent. A reply usually takes a few days.", "success")
            return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip()
    db = get_db()
    if email:
        try:
            db.execute(
                "INSERT INTO subscribers (email, created_at) VALUES (?, ?)",
                (email, datetime.now().strftime("%Y-%m-%d")),
            )
            db.commit()
            flash("You're subscribed. New episodes land in your inbox.", "success")
        except sqlite3.IntegrityError:
            flash("That email is already subscribed.", "error")
    else:
        flash("Enter an email address to subscribe.", "error")
    return redirect(request.referrer or url_for("home"))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """A lightweight 'creator dashboard' page for publishing a new episode."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        youtube_id = request.form.get("youtube_id", "").strip() or "dQw4w9WgXcQ"
        duration = request.form.get("duration", "").strip()
        thumbnail = request.form.get("thumbnail", "").strip() or (
            "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=800&q=80"
        )

        if not title or not category or not description:
            flash("Title, category, and description are required.", "error")
        else:
            db = get_db()
            db.execute(
                """INSERT INTO videos
                   (title, category, location, description, youtube_id, thumbnail,
                    duration, views, published_on)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                (
                    title, category, location, description, youtube_id,
                    thumbnail, duration, datetime.now().strftime("%Y-%m-%d"),
                ),
            )
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            flash("Episode published.", "success")
            return redirect(url_for("video_detail", video_id=new_id))

    return render_template("upload.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# --------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
