"""
Global Disaster & Emergency Events Database — Flask Web Application
Team: Krishna Koushik Thokala, Anirudh Sukumaran, Prathima Sola
AI Assistance: Claude (Anthropic, Claude Opus 4.6), April 2026
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disaster_events.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ── PAGE ROUTES ── Author: Krishna Koushik Thokala

@app.route("/")
def index():
    db = get_db()
    stats = {
        "total_disasters": db.execute("SELECT COUNT(*) FROM disasters").fetchone()[0],
        "total_countries": db.execute("SELECT COUNT(*) FROM countries").fetchone()[0],
        "total_deaths": db.execute("SELECT SUM(total_deaths) FROM disasters").fetchone()[0] or 0,
        "total_damage": db.execute("SELECT ROUND(SUM(total_damage_usd)/1000000,1) FROM disasters").fetchone()[0] or 0,
    }
    recent = db.execute("""
        SELECT d.disaster_id, d.year, d.total_deaths, d.total_affected,
               d.location, dt.type_name, c.country_name
        FROM disasters d
        JOIN disaster_types dt ON d.type_id = dt.type_id
        JOIN countries c ON d.country_id = c.country_id
        ORDER BY d.year DESC, d.disaster_id DESC LIMIT 10
    """).fetchall()
    db.close()
    return render_template("index.html", stats=stats, recent=recent)

@app.route("/explore")
def explore():
    db = get_db()
    countries = db.execute("SELECT country_id, country_name FROM countries ORDER BY country_name").fetchall()
    types = db.execute("SELECT DISTINCT type_name FROM disaster_types ORDER BY type_name").fetchall()
    db.close()
    return render_template("explore.html", countries=countries, types=types)

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/disaster/<int:disaster_id>")
def disaster_detail(disaster_id):
    """-- Author: Anirudh Sukumaran"""
    db = get_db()
    disaster = db.execute("""
        SELECT d.*, dt.type_name, dt.subtype_name, c.country_name, c.iso_code,
               r.region_name, r.continent, c.gdp_per_capita, c.income_group,
               im.no_injured, im.no_affected, im.no_homeless
        FROM disasters d
        JOIN disaster_types dt ON d.type_id = dt.type_id
        JOIN countries c ON d.country_id = c.country_id
        JOIN regions r ON c.region_id = r.region_id
        LEFT JOIN impact_metrics im ON d.disaster_id = im.disaster_id
        WHERE d.disaster_id = ?
    """, (disaster_id,)).fetchone()
    db.close()
    if not disaster:
        flash("Disaster not found.", "error")
        return redirect(url_for("explore"))
    return render_template("detail.html", d=disaster)

@app.route("/add", methods=["GET", "POST"])
def add_disaster():
    """-- Author: Anirudh Sukumaran"""
    db = get_db()
    if request.method == "POST":
        try:
            cur = db.execute("""
                INSERT INTO disasters (country_id, type_id, year, start_month, start_day,
                    location, total_deaths, total_affected, total_damage_usd)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                request.form["country_id"], request.form["type_id"],
                int(request.form["year"]),
                int(request.form["start_month"]) if request.form.get("start_month") else None,
                int(request.form["start_day"]) if request.form.get("start_day") else None,
                request.form.get("location") or None,
                int(request.form.get("total_deaths") or 0),
                int(request.form.get("total_affected") or 0),
                float(request.form.get("total_damage_usd") or 0),
            ))
            did = cur.lastrowid
            db.execute("""
                INSERT INTO impact_metrics (disaster_id, no_injured, no_affected, no_homeless)
                VALUES (?,?,?,?)
            """, (did, int(request.form.get("no_injured") or 0),
                  int(request.form.get("no_affected_detail") or 0),
                  int(request.form.get("no_homeless") or 0)))
            db.commit()
            flash("Disaster event added successfully!", "success")
            return redirect(url_for("disaster_detail", disaster_id=did))
        except Exception as e:
            db.rollback()
            flash(f"Error adding disaster: {str(e)}", "error")
    countries = db.execute("SELECT country_id, country_name FROM countries ORDER BY country_name").fetchall()
    types = db.execute("SELECT type_id, type_name, subtype_name FROM disaster_types ORDER BY type_name").fetchall()
    db.close()
    return render_template("add.html", countries=countries, types=types)

@app.route("/edit/<int:disaster_id>", methods=["GET", "POST"])
def edit_disaster(disaster_id):
    """-- Author: Anirudh Sukumaran"""
    db = get_db()
    if request.method == "POST":
        try:
            db.execute("""
                UPDATE disasters SET country_id=?, type_id=?, year=?, start_month=?, start_day=?,
                    location=?, total_deaths=?, total_affected=?, total_damage_usd=?
                WHERE disaster_id=?
            """, (
                request.form["country_id"], request.form["type_id"],
                int(request.form["year"]),
                int(request.form["start_month"]) if request.form.get("start_month") else None,
                int(request.form["start_day"]) if request.form.get("start_day") else None,
                request.form.get("location") or None,
                int(request.form.get("total_deaths") or 0),
                int(request.form.get("total_affected") or 0),
                float(request.form.get("total_damage_usd") or 0),
                disaster_id
            ))
            db.execute("""
                UPDATE impact_metrics SET no_injured=?, no_affected=?, no_homeless=?
                WHERE disaster_id=?
            """, (int(request.form.get("no_injured") or 0),
                  int(request.form.get("no_affected_detail") or 0),
                  int(request.form.get("no_homeless") or 0),
                  disaster_id))
            db.commit()
            flash("Disaster updated successfully!", "success")
            return redirect(url_for("disaster_detail", disaster_id=disaster_id))
        except Exception as e:
            db.rollback()
            flash(f"Error updating: {str(e)}", "error")
    disaster = db.execute("SELECT * FROM disasters WHERE disaster_id=?", (disaster_id,)).fetchone()
    impact = db.execute("SELECT * FROM impact_metrics WHERE disaster_id=?", (disaster_id,)).fetchone()
    countries = db.execute("SELECT country_id, country_name FROM countries ORDER BY country_name").fetchall()
    types = db.execute("SELECT type_id, type_name, subtype_name FROM disaster_types ORDER BY type_name").fetchall()
    db.close()
    return render_template("edit.html", d=disaster, im=impact, countries=countries, types=types)

@app.route("/delete/<int:disaster_id>", methods=["POST"])
def delete_disaster(disaster_id):
    """-- Author: Anirudh Sukumaran"""
    db = get_db()
    try:
        db.execute("DELETE FROM impact_metrics WHERE disaster_id=?", (disaster_id,))
        db.execute("DELETE FROM disasters WHERE disaster_id=?", (disaster_id,))
        db.commit()
        flash("Disaster deleted successfully.", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error deleting: {str(e)}", "error")
    db.close()
    return redirect(url_for("explore"))

# ── API ROUTES ── Author: Anirudh Sukumaran

@app.route("/api/search")
def api_search():
    db = get_db()
    query = """
        SELECT d.disaster_id, d.year, d.total_deaths, d.total_affected,
               d.total_damage_usd, d.location, dt.type_name, c.country_name, c.iso_code
        FROM disasters d
        JOIN disaster_types dt ON d.type_id = dt.type_id
        JOIN countries c ON d.country_id = c.country_id WHERE 1=1
    """
    params = []
    if request.args.get("country_id"):
        query += " AND d.country_id = ?"; params.append(request.args["country_id"])
    if request.args.get("type_name"):
        query += " AND dt.type_name = ?"; params.append(request.args["type_name"])
    if request.args.get("year_from"):
        query += " AND d.year >= ?"; params.append(int(request.args["year_from"]))
    if request.args.get("year_to"):
        query += " AND d.year <= ?"; params.append(int(request.args["year_to"]))
    if request.args.get("keyword"):
        kw = f"%{request.args['keyword']}%"
        query += " AND d.location LIKE ?"; params.append(kw)
    query += " ORDER BY d.year DESC, d.total_deaths DESC LIMIT 200"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/decade_trends")
def api_decade_trends():
    """-- Author: Krishna Koushik Thokala"""
    db = get_db()
    rows = db.execute("""
        SELECT (year/10)*10 AS decade, COUNT(*) AS events,
               SUM(total_deaths) AS deaths,
               ROUND(SUM(total_damage_usd)/1000,0) AS damage_millions
        FROM disasters GROUP BY decade ORDER BY decade
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/top_countries")
def api_top_countries():
    """-- Author: Prathima Sola"""
    db = get_db()
    rows = db.execute("""
        SELECT c.country_name, c.iso_code, COUNT(*) AS count, SUM(d.total_deaths) AS deaths
        FROM disasters d JOIN countries c ON d.country_id = c.country_id
        GROUP BY c.country_id ORDER BY count DESC LIMIT 15
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/type_distribution")
def api_type_distribution():
    """-- Author: Prathima Sola"""
    db = get_db()
    yr_from = request.args.get("year_from", 1900, type=int)
    yr_to = request.args.get("year_to", 2021, type=int)
    rows = db.execute("""
        SELECT dt.type_name, COUNT(*) AS count, SUM(d.total_deaths) AS deaths
        FROM disasters d JOIN disaster_types dt ON d.type_id = dt.type_id
        WHERE d.year BETWEEN ? AND ? GROUP BY dt.type_name ORDER BY count DESC
    """, (yr_from, yr_to)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/income_impact")
def api_income_impact():
    """-- Author: Prathima Sola"""
    db = get_db()
    rows = db.execute("""
        SELECT c.income_group, COUNT(*) AS count, SUM(d.total_deaths) AS deaths,
               ROUND(AVG(d.total_deaths),1) AS avg_deaths
        FROM disasters d JOIN countries c ON d.country_id = c.country_id
        WHERE c.income_group IS NOT NULL AND d.year >= 1990
        GROUP BY c.income_group ORDER BY deaths DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/monthly_pattern")
def api_monthly_pattern():
    """-- Author: Anirudh Sukumaran"""
    db = get_db()
    rows = db.execute("""
        SELECT start_month AS month, COUNT(*) AS count, SUM(total_deaths) AS deaths
        FROM disasters WHERE start_month IS NOT NULL
        GROUP BY start_month ORDER BY start_month
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/flood_trend")
def api_flood_trend():
    """-- Author: Prathima Sola"""
    db = get_db()
    rows = db.execute("""
        SELECT d.year, COUNT(*) AS count
        FROM disasters d JOIN disaster_types dt ON d.type_id = dt.type_id
        WHERE dt.type_name = 'Flood' AND d.year >= 1970
        GROUP BY d.year ORDER BY d.year
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/continent_data")
def api_continent_data():
    """Disasters by continent for map visualization. -- Author: Krishna Koushik Thokala"""
    db = get_db()
    rows = db.execute("""
        SELECT r.continent, r.region_name, c.country_name, c.iso_code,
               COUNT(*) AS count, SUM(d.total_deaths) AS deaths
        FROM disasters d
        JOIN countries c ON d.country_id = c.country_id
        JOIN regions r ON c.region_id = r.region_id
        GROUP BY c.country_id ORDER BY count DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        from init_db import init_db
        init_db(DB_PATH)
    app.run(debug=True, host="0.0.0.0", port=5000)
