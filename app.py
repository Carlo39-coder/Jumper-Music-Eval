import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# --------------------- Konfiguration ---------------------
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dein-lokaler-fallback-secret')

# Datenbank (Render PostgreSQL + lokaler SQLite)
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///jumper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Kriterien laden
with open('kriterien.json') as f:
    KRITERIEN = json.load(f)

# --------------------- Models ---------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    is_mentor = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Track(db.Model):
    __tablename__ = 'track'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    genre = db.Column(db.String(50), default="Deutschrap")
    url = db.Column(db.String(500), nullable=False)
    bonus = db.Column(db.Integer, default=0)
    datum = db.Column(db.String(50), nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    technische_qualitaet = db.Column(db.Integer, default=0)
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------------------- Routen ---------------------
@app.route('/upload')
def upload_redirect():
    return redirect(url_for('submit'))


@app.route('/leaderboard')
def leaderboard():
    return redirect(url_for('tracks'))  # oder render_template('leaderboard.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        alter = request.form.get('alter')
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username bereits vergeben.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('E-Mail bereits vergeben.')
            return redirect(url_for('register'))

        try:
            alter = int(alter)
        except (TypeError, ValueError):
            flash('Alter muss eine Zahl sein.')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            email=email,
            alter=alter,
            is_mentor=False,
            is_admin=False
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        flash('Registrierung erfolgreich! Du kannst dich jetzt einloggen.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('submit'))
        else:
            flash('Falscher Username oder Passwort.')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich ausgeloggt.')
    return redirect(url_for('index'))


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        name = request.form['name']
        genre = request.form['genre']
        link = request.form.get('link')
        track_url = ''

        if 'track' in request.files and request.files['track'].filename:
            file = request.files['track']
            upload_result = cloudinary.uploader.upload(file, resource_type="video")
            track_url = upload_result['secure_url']
        elif link:
            track_url = link
        else:
            flash('Bitte Datei hochladen oder Link angeben.')
            return redirect(url_for('submit'))

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
        flash('Track erfolgreich eingereicht!')
        return redirect(url_for('tracks'))

    return render_template('submit.html')


@app.route('/tracks')
def tracks():
    all_tracks = Track.query.all()
    return render_template('tracks.html', tracks=all_tracks)


@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
@login_required
def rate(track_id):
    if not current_user.is_mentor:
        flash('Nur Mentoren dürfen bewerten.')
        return redirect(url_for('tracks'))

    track = Track.query.get_or_404(track_id)

    if request.method == 'POST':
        try:
            h = int(request.form['historischer_bezug'])
            k = int(request.form['kreativitaet'])
            t = int(request.form['technische_qualitaet'])
            c = int(request.form['community'])
        except (KeyError, ValueError):
            flash('Bitte alle Bewertungsfelder ausfüllen.')
            return redirect(url_for('rate', track_id=track_id))

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
        flash('Bewertung gespeichert!')
        return redirect(url_for('tracks'))

    return render_template('rate.html', track=track)


@app.route('/kriterien-info')
def kriterien_info():
    return render_template('kriterien_info.html')


@app.route('/kriterien')
def kriterien():
    return render_template('kriterien.html')


@app.route('/kriterien-theorie')
def kriterien_theorie():
    return render_template('kriterien_theorie.html')
    
# ==================== TEMPORÄRE ADMIN-ROUTE ====================
# Diese Route macht deinen Account zum Admin.
# WICHTIG: Nur lokal oder kurz auf Render aufrufen!
# Danach wieder löschen und neu deployen!

@app.route('/make_me_admin')
def make_me_admin():
    if not current_user.is_authenticated:
        flash('Du musst eingeloggt sein, um Admin zu werden.')
        return redirect(url_for('login'))
    
    # ÄNDERE HIER DEINEN USERNAME ODER DEINE EMAIL AUF DEINEN ECHTEN ACCOUNT!
    if current_user.username == 'Carlo39-coder' or current_user.email == 'deine@email.de':  # <-- passe das an!
        current_user.is_admin = True
        db.session.commit()
        flash(f'{current_user.username} ist jetzt Admin! 🎉')
        return redirect(url_for('index'))
    else:
        flash('Nur der Hauptaccount darf Admin werden.')
        return redirect(url_for('index'))


# ============================================================

# --------------------- Start der App ---------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
