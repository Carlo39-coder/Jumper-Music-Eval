from flask import Flask, render_template, request, flash, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = "jumper2025"

# Globale Speicher (persistent via app.config)
app.config['SUBMISSIONS'] = []
app.config['GENRES'] = {
    "oldschool": "Old School / Boom Bap",
    "conscious": "Conscious / Politischer Rap",
    "battle": "Battle-Rap",
    "gangsta": "Gangsta- / Straßenrap",
    "poprap": "Pop-Rap / Raop",
    "emo": "Emo Rap",
    "trap": "Trap",
    "cloud": "Cloud Rap / Hashtag-Rap"
}

def get_submissions():
    if 'SUBMISSIONS' not in app.config:
        app.config['SUBMISSIONS'] = []
    return app.config['SUBMISSIONS']

def get_genres():
    return app.config['GENRES']

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        submissions = get_submissions()
        entry = {
            "name": request.form["name"],
            "alter": int(request.form["alter"]),
            "genre": request.form["genre"],
            "track": request.form["track"],
            "bonus": int(request.form["alter"]) < 25
        }
        submissions.append(entry)
        bonus_text = " (+15 % Jungkünstler-Bonus)" if entry["bonus"] else ""
        flash(f"Danke {entry['name']}! Dein Track im Genre »{get_genres()[entry['genre']]}« wurde eingereicht.{bonus_text}")
        return redirect(url_for("index"))
    return render_template("submit.html")

@app.route("/leaderboard")
def leaderboard():
    submissions = get_submissions()
    genres = get_genres()
    return render_template("leaderboard.html", submissions=submissions, genres=genres)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
