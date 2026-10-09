#!/usr/bin/env python3
"""Render the Flask site into a fully static GitHub Pages-ready output."""

from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path
from urllib.parse import quote_plus

from flask import render_template

from vlogsite.app import DB_PATH, app

REPO_ROOT = Path(__file__).resolve().parent
SITE_DIR = REPO_ROOT / "site"
CSS_SRC = REPO_ROOT / "vlogsite" / "static" / "css" / "style.css"

VIDEO_SLUGS: dict[int, str] = {}
POST_SLUGS: dict[int, str] = {}


def slugify(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or fallback


def build_slug_maps() -> None:
    global VIDEO_SLUGS, POST_SLUGS

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        videos = db.execute("SELECT id, title FROM videos ORDER BY id").fetchall()
        posts = db.execute("SELECT id, title FROM posts ORDER BY id").fetchall()

    seen_video = set()
    for row in videos:
        base = slugify(row["title"], f"video-{row['id']}")
        slug = base
        suffix = 2
        while slug in seen_video:
            slug = f"{base}-{suffix}"
            suffix += 1
        seen_video.add(slug)
        VIDEO_SLUGS[int(row["id"])] = slug

    seen_post = set()
    for row in posts:
        base = slugify(row["title"], f"post-{row['id']}")
        slug = base
        suffix = 2
        while slug in seen_post:
            slug = f"{base}-{suffix}"
            suffix += 1
        seen_post.add(slug)
        POST_SLUGS[int(row["id"])] = slug


def static_url_for(endpoint: str, **values):
    if endpoint == "static":
        filename = values.get("filename", "")
        return f"/static/{filename}"
    if endpoint == "home":
        return "/"
    if endpoint == "videos":
        params = []
        category = values.get("category")
        search = values.get("q")
        if category:
            params.append(f"category={quote_plus(str(category))}")
        if search:
            params.append(f"q={quote_plus(str(search))}")
        base = "/videos/"
        if params:
            return f"{base}?{'&'.join(params)}"
        return base
    if endpoint == "video_detail":
        video_id = int(values["video_id"])
        return f"/videos/{VIDEO_SLUGS[video_id]}/"
    if endpoint == "journal":
        return "/journal/"
    if endpoint == "journal_post":
        post_id = int(values["post_id"])
        return f"/journal/{POST_SLUGS[post_id]}/"
    if endpoint == "about":
        return "/about.html"
    if endpoint == "contact":
        return "/contact.html"
    if endpoint == "upload":
        return "/upload.html"
    if endpoint == "subscribe":
        return "/"
    return "/"


def render_static(template_name: str, request_path: str, **context):
    app.jinja_env.globals["url_for"] = static_url_for
    with app.test_request_context(request_path):
        return render_template(template_name, **context)


def write_html(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def query_db() -> tuple[list[sqlite3.Row], list[sqlite3.Row], list[sqlite3.Row], list[sqlite3.Row], sqlite3.Row]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
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
        videos = db.execute("SELECT * FROM videos ORDER BY published_on DESC").fetchall()
        posts = db.execute("SELECT * FROM posts ORDER BY published_on DESC").fetchall()
        return featured, latest_post, stats, categories, videos, posts


def generate_site() -> None:
    build_slug_maps()

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    static_dir = SITE_DIR / "static" / "css"
    static_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CSS_SRC, static_dir / "style.css")

    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
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
        videos = db.execute("SELECT * FROM videos ORDER BY published_on DESC").fetchall()
        posts = db.execute("SELECT * FROM posts ORDER BY published_on DESC").fetchall()

    # Homepage
    home_html = render_static(
        "home.html",
        "/",
        featured=featured,
        latest_post=latest_post,
        stats=stats,
        categories=categories,
    )
    write_html(SITE_DIR / "index.html", home_html)

    # About
    about_html = render_static(
        "about.html",
        "/about",
        stats=db_query_stats(),
        countries=db_query_countries(),
    )
    write_html(SITE_DIR / "about.html", about_html)

    # Contact
    contact_html = render_static("contact.html", "/contact")
    write_html(SITE_DIR / "contact.html", contact_html)

    # Upload
    upload_html = render_static("upload.html", "/upload")
    write_html(SITE_DIR / "upload.html", upload_html)

    # Videos landing page
    video_categories = get_categories()
    videos_html = render_static(
        "videos.html",
        "/videos",
        videos=videos,
        categories=video_categories,
        active_category="",
        search="",
    )
    write_html(SITE_DIR / "videos" / "index.html", videos_html)

    # Journal landing page
    journal_html = render_static("journal.html", "/journal", posts=posts)
    write_html(SITE_DIR / "journal" / "index.html", journal_html)

    # Video detail pages
    for video in videos:
        more = get_more_videos(video["category"], int(video["id"]))
        comments = get_comments_for_video(int(video["id"]))
        detail_html = render_static(
            "video_detail.html",
            f"/video/{video['id']}",
            video=video,
            comments=comments,
            more=more,
        )
        write_html(SITE_DIR / "videos" / VIDEO_SLUGS[int(video["id"])] / "index.html", detail_html)

    # Journal post pages
    for post in posts:
        others = get_other_posts(int(post["id"]))
        post_html = render_static(
            "journal_post.html",
            f"/journal/{post['id']}",
            post=post,
            others=others,
        )
        write_html(SITE_DIR / "journal" / POST_SLUGS[int(post["id"])] / "index.html", post_html)

    # 404 page
    not_found_html = render_static("404.html", "/missing")
    write_html(SITE_DIR / "404.html", not_found_html)


def db_query_stats():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            """SELECT COUNT(*) AS video_count,
                       COALESCE(SUM(views),0) AS total_views,
                       MIN(published_on) AS first_published
               FROM videos"""
        ).fetchone()


def db_query_countries():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            "SELECT DISTINCT location FROM videos WHERE location IS NOT NULL"
        ).fetchall()


def get_categories():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            "SELECT DISTINCT category FROM videos ORDER BY category"
        ).fetchall()


def get_comments_for_video(video_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            "SELECT * FROM comments WHERE video_id = ? ORDER BY created_at DESC",
            (video_id,),
        ).fetchall()


def get_more_videos(category: str, current_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            "SELECT * FROM videos WHERE category = ? AND id != ? LIMIT 3",
            (category, current_id),
        ).fetchall()


def get_other_posts(current_id: int):
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return db.execute(
            "SELECT * FROM posts WHERE id != ? ORDER BY published_on DESC LIMIT 2",
            (current_id,),
        ).fetchall()


if __name__ == "__main__":
    generate_site()
    print(f"Static site generated in {SITE_DIR}")
