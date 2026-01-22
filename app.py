import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange, Length
import cloudinary
import cloudinary.uploader
from markupsafe import Markup

# Logging einrichten
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==================================================
# Sicherheit – Secret Key & Production-Settings
# ==================================================
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY muss als Umgebungsvariable gesetzt sein!\n"
        "→ Render Dashboard → Environment → Variable 'SECRET_KEY' hinzufügen\n"
        "→ Wert z. B. mit python -c \"import secrets; print(secrets.token_hex(32))\" erzeugen"
    )

# Produktionssichere Session-Cookie-Einstellungen
app.config['SESSION_COOKIE_SECURE'] = True  # Nur HTTPS (Render erzwingt HTTPS)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 Stunde

# ==================================================
# Datenbank-Konfiguration
# ==================================================
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///jumper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from flask_migrate import Migrate
migrate = Migrate(app, db)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================================================
# Cloudinary Konfiguration
# ==================================================
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)
if not all([cloudinary.config().cloud_name, cloudinary.config().api_key, cloudinary.config().api_secret]):
    logger.warning("Cloudinary-Keys fehlen – Uploads werden fehlschlagen.")

# ==================================================
# Robuster Dateipfad + globales Cachen der Kriterien
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KRITERIEN_DATA = None
try:
    json_path = os.path.join(BASE_DIR, 'kriterien.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        KRITERIEN_DATA = json.load(f)
    logger.info(f"kriterien.json erfolgreich geladen: {json_path}")
except FileNotFoundError:
    logger.error(f"kriterien.json nicht gefunden: {json_path}")
    KRITERIEN_DATA = {}
except json.JSONDecodeError as e:
    logger.error(f"JSON-Syntaxfehler in kriterien.json: {e}")
    KRITERIEN_DATA = {}
except Exception as e:
    logger.error(f"Unerwarteter Fehler beim Laden von kriterien.json: {e}")
    KRITERIEN_DATA = {}

# ==================================================
# WTForms für Register & Login
# ==================================================
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username ist erforderlich'),
        Length(min=3, max=64, message='Username muss zwischen 3 und 64 Zeichen haben')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email ist erforderlich'),
        Email(message='Ungültige Email-Adresse')
    ])
    alter = IntegerField('Alter', validators=[
        DataRequired(message='Alter ist erforderlich'),
        NumberRange(min=13, max=100, message='Alter muss zwischen 13 und 100 liegen')
    ])
    password = PasswordField('Passwort', validators=[
        DataRequired(message='Passwort ist erforderlich'),
        Length(min=6, message='Passwort muss mindestens 6 Zeichen haben')
    ])
    submit = SubmitField('Registrieren')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Einloggen')

# ==================================================
# Models
# ==================================================
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    alter = db.Column(db.Integer, nullable=False)
    is_mentor = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        # Korrekte Einrückung + explizite Hash-Methode
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # z.B. "Deutschrap"
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Track(db.Model):
    __tablename__ = 'track'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    genre = db.Column(db.String(50), default="Deutschrap")
    url = db.Column(db.String(500), nullable=False)
    bonus = db.Column(db.Integer, default=0)
    datum = db.Column(db.Date, nullable=False)
    historischer_bezug = db.Column(db.Integer, default=0)
    kreativitaet = db.Column(db.Integer, default=0)
    technische_qualitaet = db.Column(db.Integer, default=0)
    community = db.Column(db.Integer, default=0)
    gesamt_score = db.Column(db.Float, default=0.0)
    mentor_feedback = db.Column(db.Text)
    artist = db.relationship('User', backref='tracks')
    battle_id = db.Column(db.Integer, db.ForeignKey('battle.id'), nullable=True)
    battle = db.relationship('Battle', backref='tracks')
    
class Battle(db.Model):
    __tablename__ = 'battle'
    id = db.Column(db.Integer, primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(100), nullable=False)  # z.B. "Deutschrap Battle Feb 2026"
    status = db.Column(db.String(20), default="active")  # active, voting, finished
    genre = db.relationship('Genre', backref='battles')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================================================
# Routen
# ==================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kriterien_theorie')
def kriterien_theorie():
    try:
        return render_template(
            'kriterien_theorie.html',
            kriterien=KRITERIEN_DATA,
            title="Bewertungskriterien Theorie"
        )
    except Exception as e:
        logger.error(f"Fehler beim Rendern von kriterien_theorie: {str(e)}", exc_info=True)
        flash("Interner Fehler – bitte später erneut versuchen", "danger")
        return render_template(
            'kriterien_theorie.html',
            kriterien={},
            title="Fehler"
        ), 500

@app.route('/setup-initial-genre')
def setup_initial_genre():
    if Genre.query.filter_by(name='Deutschrap').first():
        return "Deutschrap existiert bereits."
    
    deutschrap = Genre(name='Deutschrap', description='Monatliche Battles im Genre Deutschrap')
    db.session.add(deutschrap)
    db.session.commit()
    
    # Erstes Battle erstellen
    battle = Battle(
        genre_id=deutschrap.id,
        start_date=datetime(2026, 2, 1).date(),
        end_date=datetime(2026, 2, 28).date(),
        title='Deutschrap Battle Februar 2026',
        status='active'
    )
    db.session.add(battle)
    db.session.commit()
    
    return "Deutschrap + erstes Battle erfolgreich angelegt!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        alter = form.alter.data
        password = form.password.data

        if User.query.filter_by(username=username).first():
            flash('Username bereits vergeben.', 'danger')
            return render_template('register.html', form=form)

        if User.query.filter_by(email=email).first():
            flash('E-Mail bereits registriert.', 'danger')
            return render_template('register.html', form=form)

        new_user = User(
            username=username,
            email=email,
            alter=alter,
            is_mentor=False,
            is_admin=False
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registrierung erfolgreich! Du kannst dich jetzt einloggen.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registrierungsfehler: {str(e)}", exc_info=True)
            flash('Fehler beim Speichern. Bitte später erneut versuchen.', 'danger')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('submit'))
        else:
            flash('Falscher Username oder Passwort.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich ausgeloggt.', 'success')
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        name = request.form['name'].strip()
        genre = request.form['genre'].strip()
        link = request.form.get('link')
        track_url = ''

        if not name or not genre:
            flash('Name und Genre müssen ausgefüllt sein.', 'danger')
            return redirect(url_for('submit'))

        try:
            if 'track' in request.files and request.files['track'].filename:
                file = request.files['track']
                if not file.mimetype.startswith('audio/'):
                    raise ValueError("Nur Audio-Dateien erlaubt.")
                upload_result = cloudinary.uploader.upload(file, resource_type="video")
                track_url = upload_result['secure_url']
            elif link:
                track_url = link
            else:
                flash('Bitte Datei hochladen oder Link angeben.', 'danger')
                return redirect(url_for('submit'))

            bonus = 10 if current_user.alter < 25 else 0

            new_track = Track(
                name=name,
                artist_id=current_user.id,
                genre=genre,
                url=track_url,
                bonus=bonus,
                datum=datetime.now().date()
            )
            db.session.add(new_track)
            db.session.commit()
            flash('Track erfolgreich eingereicht!', 'success')
            return redirect(url_for('tracks'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Submit-Fehler: {str(e)}", exc_info=True)
            flash(f'Fehler beim Upload: {str(e)}', 'danger')

    return render_template('submit.html')

@app.route('/tracks')
@login_required
def tracks():
    if not current_user.is_admin:
        abort(403)
    all_tracks = Track.query.all()
    return render_template('tracks.html', tracks=all_tracks)

@app.route('/rate/<int:track_id>', methods=['GET', 'POST'])
@login_required
def rate(track_id):
    if not current_user.is_mentor and not current_user.is_admin:
        abort(403)
    track = Track.query.get_or_404(track_id)

    if request.method == 'POST':
        try:
            track.historischer_bezug = int(request.form.get('historischer_bezug', 0))
            track.kreativitaet = int(request.form.get('kreativitaet', 0))
            track.technische_qualitaet = int(request.form.get('technische_qualitaet', 0))
            track.community = int(request.form.get('community', 0))
            scores = [track.historischer_bezug, track.kreativitaet, track.technische_qualitaet, track.community]
            if any(s < 0 or s > 10 for s in scores):
                raise ValueError("Scores müssen zwischen 0 und 10 liegen.")
            track.mentor_feedback = request.form.get('feedback', '')
            track.gesamt_score = (sum(scores) + track.bonus) / 5.0
            db.session.commit()
            flash('Bewertung gespeichert!', 'success')
            return redirect(url_for('tracks'))
        except ValueError as e:
            flash(f'Ungültige Eingabe: {str(e)}', 'danger')
        except Exception as e:
            logger.error(f"Rate-Fehler: {str(e)}", exc_info=True)
            flash('Fehler beim Speichern der Bewertung.', 'danger')

    return render_template('rate.html', track=track, kriterien=KRITERIEN_DATA)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)

# Hilfsrouten
@app.route('/upload')
def upload_redirect():
    return redirect(url_for('submit'))

@app.route('/leaderboard')
def leaderboard():
    return redirect(url_for('tracks'))

@app.route('/db-setup')
def db_setup():
    try:
        db.create_all()  # Erstellt alle fehlenden Tabellen (Genre, Battle usw.)
        return "Datenbank-Tabellen erfolgreich erstellt! (genre, battle usw.)"
    except Exception as e:
        return f"Fehler beim Erstellen der Tabellen: {str(e)}", 500

@app.route('/fix-tracks-table')
def fix_tracks_table():
    try:
        # 1. Alte Tabelle löschen (VORSICHT: löscht ALLE Tracks!)
        db.drop_all()  # löscht alle Tabellen – nur für Test/Reset!

        # 2. Alle Tabellen neu erstellen (inkl. neuer battle_id-Spalte)
        db.create_all()

        return "Datenbank-Tabellen wurden neu erstellt! (battle_id existiert jetzt)<br>Tracks müssen neu hochgeladen werden."
    except Exception as e:
        return f"Fehler: {str(e)}", 500
# ==================================================
# Start
# ==================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Nur für lokale Entwicklung
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
