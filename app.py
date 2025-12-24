from flask import Flask, request, redirect, url_for
import import cloudinary
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Cloudinary-Konfiguration via Environment-Vars (für Render)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True  # Für HTTPS-URLs
)
# DB-Konfiguration: PostgreSQL auf Render via Env-Var, Fallback zu SQLite lokal
db_uri = os.environ.get('DATABASE_URL')
if db_uri and db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///jumper.db'

# Track-Modell für DB
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    art = db.Column(db.String(50), nullable=False)
    bonus = db.Column(db.String(50))
    datum = db.Column(db.String(50))

# Erstelle Tabellen automatisch
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return '''
    <h1 style="text-align:center; margin-top:80px;">JUMPER</h1>
    <h2 style="text-align:center; color:#ff4d4d;">Die fairste Deutschrap & Hip-Hop Plattform</h2>
    <p style="text-align:center; margin-top:50px;">
        <a href="/submit" style="padding:20px 40px; background:#ff4d4d; color:white; text-decoration:none; font-size:22px; border-radius:12px;">
            Jetzt Track einreichen
        </a>
    </p>
    <p style="text-align:center; margin-top:30px;"><a href="/tracks">Alle Tracks ansehen</a></p>
    '''

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        alter = int(request.form['alter'])
        bonus = " (+ Bonus <25)" if alter < 25 else ""
        datum = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Fall 1: Datei-Upload
        if 'track' in request.files and request.files['track'].filename:
            file = request.files['track']
            # Upload mit Custom-Context für Metadaten (Backup für Cloudinary)
            upload = cloudinary.uploader.upload(
                file,
                resource_type="video",
                folder="jumper-tracks",
                context={
                    'name': name,
                    'alter': str(alter),
                    'bonus': 'True' if alter < 25 else 'False',
                    'datum': datum
                }
            )
            track_url = upload['secure_url']
            art = "Datei-Upload"

        # Fall 2: Link
        else:
            track_url = request.form['link']
            art = "Link"

        # Speichere in DB (persistent!)
        new_track = Track(name=name, alter=alter, url=track_url, art=art, bonus=bonus, datum=datum)
        db.session.add(new_track)
        db.session.commit()

        return f'''
        <h1 style="color:green; text-align:center;">Erfolgreich eingereicht!</h1>
        <p style="text-align:center;">Dein Track ist jetzt dauerhaft gespeichert.</p>
        <p style="text-align:center;"><a href="{track_url}" target="_blank">Anhören</a></p>
        <p style="text-align:center;"><a href="/tracks">Alle Tracks ansehen</a> | <a href="/submit">Noch einen einreichen</a></p>
        '''

    # Formular (unverändert)
    return '''
    <h1 style="text-align:center;">Track einreichen</h1>
    <form method="post" enctype="multipart/form-data" style="text-align:center; margin:50px auto; max-width:500px; font-size:18px;">
        <p>Name/Künstlername:<br><input type="text" name="name" required style="width:100%; padding:10px;"></p>
        <p>Alter:<br><input type="number" name="alter" required style="width:100%; padding:10px;"></p>
        
        <p><b>Direkt MP3 hochladen</b> (empfohlen):<br>
           <input type="file" name="track" accept="audio/*" style="width:100%; padding:10px;"></p>
        
        <p><i>oder</i> SoundCloud/YouTube-Link:<br>
           <input type="text" name="link" placeholder="https://..." style="width:100%; padding:10px;"></p>
        
        <p><input type="submit" value="Einreichen" style="padding:15px 40px; font-size:18px; background:#ff4d4d; color:white; border:none; border-radius:10px;"></p>
    </form>
    <p style="text-align:center;"><a href="/">Zurück</a></p>
    '''

@app.route('/tracks')
def tracks():
    # Hole aus DB (persistent und vollständig)
    all_tracks = Track.query.all()

    if not all_tracks:
        return '<h2 style="text-align:center;">Noch keine Tracks hochgeladen</h2><p style="text-align:center;"><a href="/submit">Jetzt einreichen!</a></p>'

    liste = "<h1 style='text-align:center;'>Eingereichte Tracks</h1><ol style='max-width:700px; margin:40px auto; font-size:18px;'>"
    for track in all_tracks:
        liste += f"<li><b>{track.name}</b> ({track.alter} Jahre{track.bonus})<br><a href='{track.url}' target='_blank'>Anhören / Download</a><br>Eingereicht: {track.datum}</li><hr>"
    liste += "</ol><p style='text-align:center;'><a href='/submit'>Weiter einreichen</a></p>"
    return liste

if __name__ == '__main__':
    app.run(debug=True)
