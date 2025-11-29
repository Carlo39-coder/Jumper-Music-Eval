import cloudinary
import cloudinary.uploader
from flask import request

# Cloudinary einmalig konfigurieren
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Deine Route, wo der Track hochgeladen wird
@app.route('/submit', methods=
'POST':
        # Prüfen ob Datei vorhanden ist
        if 'track' not in request.files:
            return "Keine Datei ausgewählt", 400
        file = request.files['track']
        if file.filename == '':
            return "Keine Datei ausgewählt", 400

        # Das ist der neue Teil – hochladen zu Cloudinary statt runterladen!
        upload_result = cloudinary.uploader.upload(
            file,
            resource_type="video",        # wichtig für MP3, WAV, M4A etc.
            folder="jumper-tracks"        # ordnet alles schön in einen Ordner
        )
        track_url = upload_result['secure_url']

        # Schöne Erfolgsmeldung statt Download
        return f'''
        <h1 style="color:green; text-align:center;">Track erfolgreich eingereicht!</h1>
        <p style="text-align:center; font-size:120%;">
            Dein Track ist jetzt dauerhaft gespeichert und verschwindet nie mehr.
        </p>
        <p style="text-align:center;">
            <a href="{track_url}" target="_blank">Direkt anhören / herunterladen</a>
        </p>
        <p style="text-align:center; margin-top:40px;">
            <a href="/submit">Noch einen einreichen</a> | 
            <a href="/">Zur Startseite</a>
        </p>
        '''
    
    # Dein bisheriger GET-Teil (Formular anzeigen) bleibt einfach so wie er ist
    return ''' ... dein bisheriges Formular ... '''
