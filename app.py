```python
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import json
import datetime

app = Flask(__name__)

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

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/anmelden', methods=['POST'])
def anmelden():
    name = request.form['name']
    age = int(request.form['age'])
    track = request.form['track']
    genre = request.form['genre']
    month = datetime.date.today().strftime("%Y-%m")

    # Jugend-Bonus
    bonus = 10 if age < 25 else 0

    # Dummy-Werte (später echte Analyse)
    punkte = {"historischer_bezug": 85, "kreativitaet": 88, "technische_qualitaet": 90, "community_feedback": 75}
    kriterien = default_criteria
    score = sum(punkte[k] * kriterien[k] for k in kriterien) + bonus

    conn = sqlite3.connect('jumper.db')
    c = conn.cursor()
    c.execute("INSERT INTO artists (name, age, track, genre, month, score) VALUES (?, ?, ?, ?, ?, ?)",
              (name, age, track, genre, month, score))
    conn.commit()
    conn.close()

    return f"<h2>Danke, {name}!</h2>Dein vorläufiger Score: {score:.1f} Punkte (Platzierung wird laufend aktualisiert)"

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('jumper.db')
    c = conn.cursor()
    c.execute("SELECT name, track, score FROM artists ORDER BY score DESC LIMIT 20")
    top = c.fetchall()
    conn.close()
    liste = "<ol>" + "".join(f"<li><strong>{row[0]}</strong> – {row[1]} → {row[2]} Punkte</li>" for row in top) + "</ol>"
    return f"<h1>Leaderboard dieses Monats</h1>{liste}<br><a href='/'>Neue Anmeldung</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
