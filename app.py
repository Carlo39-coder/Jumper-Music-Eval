from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'your_secret_key'  # Für Sessions/Login

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

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Lade Kriterien
with open('kriterien.json') as f:
    KRITERIEN = json.load(f)

# User Model
# User Model (für Artists/Mentoren)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    is_mentor = db.Column(db.Boolean, default=False)  # Für Bewertungsrechte
    verified = db.Column(db.Boolean, default=True)  # Sofort verified nach Registrierung

# Track Model
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    genre = db.Column(db.String(50), default="Deutschrap")  # Neu: Genre
    url = db.Column(db.String(500), nullable=False)
    bonus = db.Column(db.Integer, default=0)  # Neu: Integer für +10 U25
    datum = db.Column(db.String(50), nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    technische_qualitaet = db.Column(db.Integer, default=0)  # Neu: 15%
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')  # Jetzt Template rendern!

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        alter = int(request.form['alter'])
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, alter=alter, password_hash=hashed_pw, verified=True)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('submit'))
    return render_template('register.html')  # Erstelle register.html im templates/ (kopiere inline HTML dorthin)

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
    return render_template('login.html')  # Erstelle login.html (kopiere inline)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
@login_required  # Jetzt geschützt!
def submit():
    if not current_user.verified:
        return "Bitte verifiziere deinen Account."
    if request.method == 'POST':
        name = request.form['name']
        genre = request.form['genre']
        link = request.form.get('link')
        track_url = ''
        if 'track' in request.files and request.files['track'].filename != '':
            file = request.files['track']
            upload_result = cloudinary.uploader.upload(file, resource_type="video")
            track_url = upload_result['secure_url']
        elif link:
            track_url = link
        else:
            return "Fehler: Keine Datei oder Link."
        bonus = 10 if current_user.alter < 25 else 0
        new_track = Track(
            name=name,
            artist_id=current_user.id,
            genre=genre,
            url=track_url,
            bonus=bonus,
            datum=datetime.now().strftime("%d.%m.%Y")
        )
        db.session.add(new_track)
        db.session.commit()
        return redirect(url_for('tracks'))
    return render_template('submit.html')  # Verwende Template!

@app.route('/tracks')
def tracks():
    all_tracks = Track.query.all()
    return render_template('tracks.html', tracks=all_tracks)  # Verwende Template!

@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
@login_required
def rate(track_id):
    if not current_user.is_mentor:
        return "Nur Mentoren können bewerten."
    track = Track.query.get_or_404(track_id)
    if request.method == 'POST':
        h = int(request.form['historischer_bezug'])
        k = int(request.form['kreativitaet'])
        t = int(request.form['technische_qualitaet'])
        c = int(request.form['community'])
        weights = KRITERIEN.get(track.genre, KRITERIEN['Deutschrap'])
        track.historischer_bezug = h
        track.kreativitaet = k
        track.technische_qualitaet = t
        track.community = c
        track.gesamt_score = (
            h * weights['historischer_bezug'] * 10 +
            k * weights['kreativitaet'] * 10 +
            t * weights['technische_qualitaet'] * 10 +
            c * weights['community'] * 10 +
            track.bonus
        )
        track.mentor_feedback = request.form.get('feedback', '')
        db.session.commit()
        return redirect(url_for('tracks'))
    return render_template('rate.html', track=track)  # Erstelle rate.html (kopiere inline Form)

if __name__ == '__main__':
    app.run(debug=True)
