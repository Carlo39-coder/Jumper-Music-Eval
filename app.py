from flask import Flask, render_template, request, flash, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = "jumper2025"

# Globale Variablen (persistent in Render)
submissions = []
GENRES = {
    "oldschool": "Old School / Boom Bap",
    "conscious": "Conscious / Politischer Rap",
    "battle": "Battle-Rap",
    "gangsta": "Gangsta- / Straßenrap",
    "poprap": "Pop-Rap / Raop",
    "emo": "Emo Rap",
    "trap": "Trap",
    "cloud": "Cloud Rap / Hashtag-Rap"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        entry = {
            "name": request.form["name"],
            "alter": int(request.form["alter"]),
            "genre": request.form["genre"],
            "track": request.form["track"],
            "bonus": int(request.form["alter"]) < 25
        }
        submissions.append(entry)
        bonus_text = " (+15 % Jungkünstler-Bonus)" if entry["bonus"] else ""
        genre_name = GENRES.get(entry["genre"], entry["genre"])
        flash(f"Danke {entry['name']}! Dein Track im Genre »{genre_name}« wurde eingereicht.{bonus_text}")
        return redirect(url_for("index"))
    return render_template("submit.html")

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", submissions=submissions, genres=GENRES)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
