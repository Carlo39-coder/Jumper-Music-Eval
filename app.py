from flask import Flask, request
import cloudinary
import cloudinary.uploader
import os

app = Flask(__name__)

# Cloudinary automatisch aus Render-Variablen laden
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@app.route('/')
def home():
    return '''
    <h1 style="text-align:center; margin-top:100px;">JUMPER</h1>
    <h2 style="text-align:center; color:#ff4d4d;">Die fairste Deutschrap & Hip-Hop Plattform</h2>
    <p style="text-align:center; font-size:120%; margin-top:50px;">
        <a href="/submit" style="padding:20px 40px; background:#ff4d4d; color:white; text-decoration:none; font-size:20px; border-radius:12px;">
            Jetzt Track einreichen
        </a>
    </p>
    '''

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        if 'track' not in request.files:
            return '<h3>Keine Datei ausgewählt</h3><a href="/submit">Zurück</a>'
        
        file = request.files['track']
        if file.filename == '':
            return '<h3>Keine Datei ausgewählt</h3><a href="/submit">Zurück</a>'

        # Hochladen zu Cloudinary → dauerhaft gespeichert!
        result = cloudinary.uploader.upload(
            file,
            resource_type="video",
            folder="jumper-tracks"
        )
        url = result['secure_url']

        return f'''
        <h1 style="color:green; text-align:center;">Erfolgreich eingereicht!</h1>
        <p style="text-align:center; font-size:120%;">
            Dein Track ist jetzt für immer gespeichert.
        </p>
        <p style="text-align:center;">
            <a href="{url}" target="_blank">Direkt anhören / herunterladen</a>
        </p>
        <p style="text-align:center; margin-top:40px;">
            <a href="/submit">Noch einen einreichen</a> | 
            <a href="/">Startseite</a>
        </p>
        '''

    return '''
    <h1 style="text-align:center;">Track einreichen</h1>
    <form method="post" enctype="multipart/form-data" style="text-align:center; margin-top:50px;">
        <p><input type="file" name="track" accept="audio/*" required style="font-size:18px;"></p>
        <p><input type="submit" value="Hochladen & einreichen" style="padding:15px 40px; font-size:18px; background:#ff4d4d; color:white; border:none; border-radius:10px;"></p>
    </form>
    <p style="text-align:center; margin-top:50px;"><a href="/">← Zurück</a></p>
    '''

if __name__ == '__main__':
    app.run(debug=True)
