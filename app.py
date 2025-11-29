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
@app.route('/submit', methods=['POST'])
def submit_track():
    if 'track' not in request.files:
        return "Kein Track hochgeladen"
    
    datei = request.files['track']
    
    # Hochladen zu Cloudinary (das passiert in Sekundenschnelle)
    upload_ergebnis = cloudinary.uploader.upload(datei, resource_type="video")  # "video" weil MP3/MP4
    
    track_url = upload_ergebnis['secure_url']   # das ist der dauerhafte Link
    
    # Hier speicherst du jetzt nur noch den Link (z. B. in einer Liste oder später in einer Datenbank)
    print("Track dauerhaft gespeichert unter:", track_url)
    
    return "Track erfolgreich hochgeladen und gespeichert!"
