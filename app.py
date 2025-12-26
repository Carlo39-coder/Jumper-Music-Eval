from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        song = request.form.get("song")
        # hier später Analyse
    return render_template("index.html")

if __name__ == "__main__":
    app.run()

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)
    secure=True  # Für HTTPS-URLs
)

# DB-Konfiguration: PostgreSQL auf Render via Env-Var, Fallback zu SQLite lokal
db_uri = os.environ.get('DATABASE_URL')
if db_uri and db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///jumper.db'

db = SQLAlchemy(app)  # Initialisiere db hier

# Track-Modell für DB
class Track(db.Model):
    # ... deine bestehenden Felder ...
    historischer_bezug = db.Column(db.Integer, default=0)  # Score 0-10
    kreativitaet = db.Column(db.Integer, default=0)        # Score 0-10
    community = db.Column(db.Integer, default=0)           # Score 0-10
    gesamt_score = db.Column(db.Float, default=0.0)        # Berechneter Score
    mentor_feedback = db.Column(db.Text)                   # Optionaler Text

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
    all_tracks = Track.query.order_by(Track.datum.desc()).all()  # neueste Tracks oben.

    if not all_tracks:
        return '<h2 style="text-align:center;">Noch keine Tracks hochgeladen</h2><p style="text-align:center;"><a href="/submit">Jetzt einreichen!</a></p>'

    liste = "<h1 style='text-align:center;'>Eingereichte Tracks</h1><ol style='max-width:700px; margin:40px auto; font-size:18px;'>"
    for track in all_tracks:
        liste += f"<li><b>{track.name}</b> ({track.alter} Jahre{track.bonus})<br><a href='{track.url}' target='_blank'>Anhören / Download</a><br>Eingereicht: {track.datum}</li><hr>"
    liste += "</ol><p style='text-align:center;'><a href='/submit'>Weiter einreichen</a></p>"
    return liste

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render-Port oder Fallback auf 5000 lokal
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False für Production
@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
def rate(track_id):
    track = Track.query.get_or_404(track_id)
    if request.method == 'POST':
        # Hole Form-Daten
        track.historischer_bezug = int(request.form['historischer_bezug']) * 2  # Höheres Gewicht (x2)
        track.kreativitaet = int(request.form['kreativitaet'])
        track.community = int(request.form['community'])
        bonus = 5 if track.alter < 25 else 0  # Extra-Bonus Punkte
        track.gesamt_score = (track.historischer_bezug + track.kreativitaet + track.community + bonus) / 4.0  # Durchschnitt, anpassen
        track.mentor_feedback = request.form.get('feedback')
        db.session.commit()
        return redirect(url_for('tracks'))
    
    # Formular für Bewertung (einfaches HTML)
    return f'''
    <h1>Bewerte Track: {track.name}</h1>
    <form method="post">
        <p>Historischer Bezug (0-10, höchstes Gewicht): <input type="number" name="historischer_bezug" min="0" max="10"></p>
        <p>Kreativität (0-10): <input type="number" name="kreativitaet" min="0" max="10"></p>
        <p>Community (0-10): <input type="number" name="community" min="0" max="10"></p>
        <p>Mentor-Feedback: <textarea name="feedback"></textarea></p>
        <input type="submit" value="Bewerten">
    </form>
    '''

# In der tracks()-Funktion, in der Loop:
liste += f"<li><b>{track.name}</b> ({track.alter} Jahre{track.bonus}) - Score: {track.gesamt_score}<br><a href='{track.url}'>Anhören</a> | <a href='/rate/{track.id}'>Bewerten</a><br>Eingereicht: {track.datum}</li><hr>"
