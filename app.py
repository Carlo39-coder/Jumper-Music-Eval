from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# Database Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')  # Render setzt DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Track-Modell (ersetzt deine in-memory Liste)
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(100), nullable=False)
    artist_age = db.Column(db.Integer)
    track_title = db.Column(db.String(200), nullable=False)
    track_url = db.Column(db.String(500), nullable=False)
    genre = db.Column(db.String(50))

    def __repr__(self):
        return f"<Track {self.track_title}>"
        
# Cloudinary-Konfiguration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# DB-Konfiguration: PostgreSQL auf Render via Env-Var, Fallback zu SQLite lokal
db_uri = os.environ.get('DATABASE_URL')
if db_uri and db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///jumper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Track-Modell für DB (vollständig)
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    art = db.Column(db.String(50), nullable=False)
    bonus = db.Column(db.String(50), default="")
    datum = db.Column(db.String(50), nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)

# Erstelle Tabellen automatisch
with app.app_context():
    db.create_all()

# Gemeinsamer CSS für alle Seiten (responsive)
common_css = """
body { font-family: sans-serif; margin: 0; padding: 10px; text-align: center; }
h1, h2 { margin: 20px 0; }
a { color: #ff4d4d; text-decoration: none; padding: 10px; display: inline-block; }
form { max-width: 90%; margin: 0 auto; }
input, textarea { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
@media (max-width: 600px) { body { padding: 5px; } a { padding: 15px; font-size: 18px; } }
"""

@app.route('/')
def home():
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>JUMPER</title>
        <style>{common_css}</style>
    </head>
    <body>
        <h1>JUMPER</h1>
        <h2>Die fairste Deutschrap & Hip-Hop Plattform</h2>
        <p><a href="/submit" style="background:#ff4d4d; color:white; border-radius:12px;">Jetzt Track einreichen</a></p>
        <p><a href="/tracks">Alle Tracks ansehen</a></p>
    </body>
    </html>
    '''

@app.route('/submit', methods=['GET', 'POST'])
def submit():
        if request.method == 'POST':
        artist_name = request.form['artist_name']
        artist_age = request.form.get('artist_age', type=int)
        track_title = request.form['track_title']
        track_url = request.form['track_url']
        genre = request.form.get('genre', '')

        # Neu: In DB speichern statt in Liste
        new_track = Track(
            artist_name=artist_name,
            artist_age=artist_age,
            track_title=track_title,
            track_url=track_url,
            genre=genre
        )
        db.session.add(new_track)
        db.session.commit()

        return redirect(url_for('tracks'))

    return render_template('submit.html')

            new_track = Track(name=name, alter=alter, url=track_url, art=art, bonus=bonus, datum=datum)
            db.session.add(new_track)
            db.session.commit()

            return f'''
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Erfolg</title>
                <style>{common_css}</style>
            </head>
            <body>
                <h1 style="color:green;">Erfolgreich eingereicht!</h1>
                <p>Dein Track ist gespeichert.</p>
                <p><a href="{track_url}" target="_blank">Anhören</a></p>
                <p><a href="/tracks">Tracks ansehen</a> | <a href="/submit">Noch einen</a></p>
            </body>
            </html>
            '''
        except Exception as e:
            return f"Fehler: {str(e)}"

    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Track einreichen</title>
        <style>{common_css}</style>
    </head>
    <body>
        <h1>Track einreichen</h1>
        <form method="post" enctype="multipart/form-data">
            <p>Name:<br><input type="text" name="name" required></p>
            <p>Alter:<br><input type="number" name="alter" required></p>
            <p><b>MP3 hochladen:</b><br><input type="file" name="track" accept="audio/*"></p>
            <p><i>oder</i> Link:<br><input type="text" name="link"></p>
            <p><input type="submit" value="Einreichen" style="background:#ff4d4d; color:white; border-radius:10px;"></p>
        </form>
        <p><a href="/">Zurück</a></p>
    </body>
    </html>
    '''

@app.route('/tracks')
def tracks():
    all_tracks = Track.query.order_by(Track.id.desc()).all()  # Neueste zuerst
    return render_template('tracks.html', tracks=all_tracks)
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Keine Tracks</title>
            <style>{common_css}</style>
        </head>
        <body>
            <h2>Noch keine Tracks</h2>
            <p><a href="/submit">Einreichen!</a></p>
        </body>
        </html>
        '''

    liste = "<h1>Eingereichte Tracks</h1><ol style='list-style-type: decimal; padding: 0 20px; text-align: left; max-width: 100%;'>"
    for track in all_tracks:
        score_text = f"{track.gesamt_score}" if track.gesamt_score > 0 else "Nicht bewertet"
        liste += f"<li style='margin-bottom: 20px;'><b>{track.name}</b> ({track.alter} Jahre{track.bonus}) - Score: {score_text}<br><a href='{track.url}'>Anhören</a> | <a href='/rate/{track.id}'>Bewerten</a><br>Eingereicht: {track.datum}</li><hr>"
    liste += "</ol><p><a href='/submit'>Weiter einreichen</a></p>"

    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Tracks</title>
        <style>{common_css}</style>
    </head>
    <body>
        {liste}
    </body>
    </html>
    '''

@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
def rate(track_id):
    track = Track.query.get_or_404(track_id)
    if request.method == 'POST':
        try:
            track.historischer_bezug = int(request.form['historischer_bezug'])
            track.kreativitaet = int(request.form['kreativitaet'])
            track.community = int(request.form['community'])
            bonus = 5 if track.alter < 25 else 0
            track.gesamt_score = (track.historischer_bezug * 2 + track.kreativitaet + track.community + bonus) / 5.0
            track.mentor_feedback = request.form.get('feedback')
            db.session.commit()
            return redirect(url_for('tracks'))
        except ValueError:
            return "Fehler: Scores 0-10."

    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Bewerten</title>
        <style>{common_css}</style>
    </head>
    <body>
        <h1>Bewerte: {track.name}</h1>
        <form method="post">
            <p>Historischer Bezug (0-10): <input type="number" name="historischer_bezug" min="0" max="10"></p>
            <p>Kreativität (0-10): <input type="number" name="kreativitaet" min="0" max="10"></p>
            <p>Community (0-10): <input type="number" name="community" min="0" max="10"></p>
            <p>Feedback: <textarea name="feedback"></textarea></p>
            <input type="submit" value="Bewerten" style="background:#ff4d4d; color:white; border-radius:10px;">
        </form>
    </body>
    </html>
    '''

# Erstellt die Tabelle beim ersten Start
with app.app_context():
    db.create_all()



