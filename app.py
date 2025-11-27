```python
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import json
import datetime

app = Flask(__name__)
if not hasattr(app, 'submissions'):
    app.submissions = []
submissions = app.submissions
# Datenbank anlegen
def init_db():
    conn = sqlite3.connect('jumper.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS artists 
                 (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, track TEXT, genre TEXT, month TEXT, score REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS criteria (genre TEXT, weights TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mentors (name TEXT, years_active INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Standard-Kriterien (stark Geschichte gewichtet)
default_criteria = {"historischer_bezug": 0.5, "kreativitaet": 0.25, "technische_qualitaet": 0.15, "community_feedback": 0.1}

HTML = '''
<h1>Jumper – Anmeldung</h1>
<form action="/anmelden" method="post">
    Künstlername: <input name="name" required><br><br>
    Alter: <input type="number" name="age" required><br><br>
    Track/Album: <input name="track" required><br><br>
    Genre: <input name="genre" value="Deutschrap" required><br><br>
    <button type="submit">Anmelden & bewerten lassen</button>
</form>
<hr>
<a href="/leaderboard">Zum aktuellen Monats-Leaderboard</a>
'''

@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        name = request.form["name"]
        alter = int(request.form["alter"])
        genre = request.form["genre"]
        track = request.form["track"]
        
        # Später hier speichern (Datenbank oder Liste)
        bonus = " (+15 % Jungkünstler-Bonus)" if alter < 25 else ""
        flash(f"Danke {name}! Dein Track im Genre »{genre}« wurde eingereicht.{bonus}")
        return redirect(url_for("index"))
    return render_template("submit.html")
