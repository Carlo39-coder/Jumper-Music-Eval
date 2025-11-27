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
        
        # WICHTIG: statt flash + redirect → render_template mit Nachricht
        return render_template("submit_success.html",
                               name=entry["name"],
                               genre=genre_name,
                               bonus_text=bonus_text)

    return render_template("submit.html")
