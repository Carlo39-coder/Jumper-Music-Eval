from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model (für Artists und Mentoren)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    alter = db.Column(db.Integer)  # Für Artists
    is_mentor = db.Column(db.Boolean, default=False)  # Rolle: True für Bewertungsrechte
    verified = db.Column(db.Boolean, default=False)  # Verifikation (z.B. nach Email-Confirm)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Erweitertes Track Model (füge technische_qualitaet & genre hinzu)
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link zu User
    genre = db.Column(db.String(50), default="Deutschrap")  # Wählbar: Deutschrap oder Hip-Hop
    url = db.Column(db.String(500), nullable=False)
    bonus = db.Column(db.Integer, default=0)  # +10 für U25
    datum = db.Column(db.String(50), nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    technische_qualitaet = db.Column(db.Integer, default=0)  # Neu: 15%
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)
    
# Database Configuration (Render-compatible)
db_uri = os.environ.get('DATABASE_URL')
if db_uri and db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///jumper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Track Model
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    art = db.Column(db.String(50), default="Hip-Hop/Deutschrap")
    bonus = db.Column(db.String(50), default="")
    datum = db.Column(db.String(50), nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)

# Common CSS
common_css = """
body { font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f9f9f9; text-align: center; }
h1, h2 { color: #333; }
a { color: #ff4d4d; text-decoration: none; font-weight: bold; }
input, textarea, select { width: 100%; max-width: 500px; padding: 12px; margin: 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 8px; }
input[type="submit"] { background: #ff4d4d; color: white; font-size: 18px; border: none; border-radius: 12px; cursor: pointer; }
form { display: inline-block; text-align: left; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
@media (max-width: 600px) { body { padding: 10px; } form { padding: 15px; } }
"""

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>JUMPER</title>
        <style>{common_css}</style>
    </head>
    <body>
        <h1>JUMPER</h1>
        <h2>Die fairste Deutschrap & Hip-Hop Plattform</h2>
        <p><a href="/submit" style="background:#ff4d4d; color:white; padding:15px 30px; border-radius:12px; font-size:20px;">Jetzt Track einreichen</a></p>
        <p><a href="/tracks">Alle Tracks ansehen</a></p>
    </body>
    </html>
    '''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        alter = int(request.form['alter'])
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, alter=alter, password_hash=hashed_pw, verified=True)  # Sofort verified
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('submit'))
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Registrieren</title><style>{common_css}</style></head>
    <body>
        <h1>Artist registrieren</h1>
        <form method="post">
            <p>Username:<br><input type="text" name="username" required></p>
            <p>Email:<br><input type="email" name="email" required></p>
            <p>Alter:<br><input type="number" name="alter" min="10" max="100" required></p>
            <p>Passwort:<br><input type="password" name="password" required></p>
            <p><input type="submit" value="Registrieren"></p>
        </form>
        <p>Bereits registriert? <a href="/login">Login</a></p>
    </body>
    </html>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        alter = int(request.form['alter'])
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, alter=alter, password_hash=hashed_pw, verified=True)  # Sofort verified
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('submit'))
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Registrieren</title><style>{common_css}</style></head>
    <body>
        <h1>Artist registrieren</h1>
        <form method="post">
            <p>Username:<br><input type="text" name="username" required></p>
            <p>Email:<br><input type="email" name="email" required></p>
            <p>Alter:<br><input type="number" name="alter" min="10" max="100" required></p>
            <p>Passwort:<br><input type="password" name="password" required></p>
            <p><input type="submit" value="Registrieren"></p>
        </form>
        <p>Bereits registriert? <a href="/login">Login</a></p>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('submit'))
        return "Falsche Credentials. <a href='/login'>Versuch erneut</a>"
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Login</title><style>{common_css}</style></head>
    <body>
        <h1>Artist Login</h1>
        <form method="post">
            <p>Username:<br><input type="text" name="username" required></p>
            <p>Passwort:<br><input type="password" name="password" required></p>
            <p><input type="submit" value="Login"></p>
        </form>
        <p>Noch kein Account? <a href="/register">Registrieren</a></p>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        try:
            name = request.form['name']
            alter = int(request.form['alter'])
            link = request.form.get('link')
            track_url = ''

            if 'track' in request.files and request.files['track'].filename != '':
                file = request.files['track']
                upload_result = cloudinary.uploader.upload(file, resource_type="video")  # Audio uploads use 'video' resource_type in Cloudinary
                track_url = upload_result['secure_url']
            elif link:
                track_url = link
            else:
                return "<h2>Fehler: Keine Datei oder Link angegeben.</h2><p><a href='/submit'>Zurück</a></p>"

            bonus_text = " (U25-Bonus)" if alter < 25 else ""
            new_track = Track(
                name=name,
                alter=alter,
                url=track_url,
                bonus=bonus_text,
                datum=datetime.now().strftime("%d.%m.%Y"),
                art="Hip-Hop/Deutschrap"
            )
            db.session.add(new_track)
            db.session.commit()
            return f'''
            <!DOCTYPE html>
            <html lang="de">
            <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Erfolg</title><style>{common_css}</style></head>
            <body>
                <h1 style="color:green;">✓ Erfolgreich eingereicht!</h1>
                <p><b>{name}</b> ({alter} Jahre{bonus_text})</p>
                <p><a href="{track_url}" target="_blank">Anhören</a></p>
                <p><a href="/tracks">Alle Tracks ansehen</a> | <a href="/submit">Noch einen einreichen</a> | <a href="/">Startseite</a></p>
            </body>
            </html>
            '''
        except Exception as e:
            return f"<h2>Fehler: {str(e)}</h2><p><a href='/submit'>Zurück</a></p>"
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
            <p>Alter:<br><input type="number" name="alter" min="10" max="100" required></p>
            <p><b>MP3 hochladen:</b><br><input type="file" name="track" accept="audio/*"></p>
            <p><i>oder</i> Link (z.B. SoundCloud, YouTube):<br><input type="text" name="link" placeholder="https://..."></p>
            <p><input type="submit" value="Einreichen"></p>
        </form>
        <p><a href="/">← Zurück</a></p>
    </body>
    </html>
    '''

@app.route('/tracks')
def tracks_view():
    all_tracks = Track.query.all()
    if not all_tracks:
        return f'''
        <!DOCTYPE html>
        <html lang="de">
        <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Tracks</title><style>{common_css}</style></head>
        <body>
            <h2>Noch keine Tracks eingereicht</h2>
            <p><a href="/submit">Als Erster einreichen!</a></p>
            <p><a href="/">Startseite</a></p>
        </body>
        </html>
        '''
    liste = "<h1>Eingereichte Tracks</h1><ol style='text-align:left; max-width:600px; margin:0 auto;'>"
    for track in all_tracks:
        score = f"{track.gesamt_score:.1f}" if track.gesamt_score > 0 else "Nicht bewertet"
        liste += f"""
        <li style='background:white; padding:15px; margin:15px 0; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.1);'>
            <b>{track.name}</b> ({track.alter} Jahre{track.bonus})<br>
            Eingereicht: {track.datum}<br>
            Score: <b>{score}</b><br>
            <a href='{track.url}' target='_blank'>Anhören</a> |
            <a href='/rate/{track.id}'>Bewerten</a>
        </li>
        """
    liste += "</ol><p><a href='/submit'>Weiter einreichen</a> | <a href='/'>Startseite</a></p>"
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Tracks</title><style>{common_css}</style></head>
    <body>{liste}</body>
    </html>
    '''

@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
def rate(track_id):
    track = Track.query.get_or_404(track_id)
    if request.method == 'POST':
        try:
            h = int(request.form['historischer_bezug'])
            k = int(request.form['kreativitaet'])
            c = int(request.form['community'])
            if not all(0 <= x <= 10 for x in [h, k, c]):
                return "Fehler: Werte müssen zwischen 0 und 10 liegen."
            bonus = 5 if track.alter < 25 else 0
            track.historischer_bezug = h
            track.kreativitaet = k
            track.community = c
            track.gesamt_score = (h * 2 + k + c + bonus) / 5.0
            track.mentor_feedback = request.form.get('feedback', '')
            db.session.commit()
            return redirect(url_for('tracks_view'))
        except:
            return "Fehler bei der Eingabe."
    return f'''
    <!DOCTYPE html>
    <html lang="de">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Bewerten</title><style>{common_css}</style></head>
    <body>
        <h1>Bewerte: {track.name} ({track.alter} Jahre{track.bonus})</h1>
        <form method="post">
            <p>Historischer Bezug (0-10):<br><input type="number" name="historischer_bezug" min="0" max="10" required></p>
            <p>Kreativität (0-10):<br><input type="number" name="kreativitaet" min="0" max="10" required></p>
            <p>Community-Beitrag (0-10):<br><input type="number" name="community" min="0" max="10" required></p>
            <p>Mentor-Feedback (optional):<br><textarea name="feedback" rows="4"></textarea></p>
            <p><input type="submit" value="Bewertung absenden"></p>
        </form>
        <p><a href="/tracks">← Zurück zur Liste</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
