from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit")
def submit_form():
    return render_template("submit.html")

# ← ← ← DAS IST DIE WICHTIGE NEUE ROUTE ← ← ←
@app.route("/submit", methods=["POST"])
def submit_post():
    name = request.form.get("name", "Unbekannt")
    age = request.form.get("age", "??")
    link = request.form.get("link", "")

    # Einfach nur zur Bestätigung, dass es funktioniert
    return f"""
    <h1 style="color:#ff0044; text-align:center; margin-top:100px;">
        ERFOLG! 🔥
    </h1>
    <div style="text-align:center; color:white; font-family:sans-serif;">
        <h2>{name} ({age} Jahre)</h2>
        <p>Dein Track: <a href="{link}" style="color:#ff0044;">{link}</a></p>
        <hr style="border-color:#ff0044;">
        <h3>Die KI-Auswertung kommt im nächsten Schritt – läuft!</h3>
        <a href="/submit" style="color:#888;">← Noch einen einreichen</a>
    </div>
    """

if __name__ == "__main__":
    app.run(debug=True)
