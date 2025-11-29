from flask import Flask, request, redirect, url_for
import cloudinary.uploader
import os
from datetime import datetime

app = Flask(__name__)

# Einfache In-Memory-Datenbank (wird später durch echte PostgreSQL ersetzt)
tracks = []

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
        link = request.form['link']

        # Bonus für unter 25
        bonus = " (+ Bonus <25)" if alter < 25 else ""

        # Track speichern
        tracks.append({
            'name': name,
            'alter': alter,
            'link': link,
            'bonus': bonus,
            'datum': datetime.now().strftime("%d.%m.%Y %H:%M")
        })

        return '''
        <h1 style="color:green; text-align:center;">Erfolgreich eingereicht!</h1>
        <p style="text-align:center; font-size:120%;">Dein Track ist jetzt in der Bewertung.</p>
        <p style="text-align:center;"><a href="/tracks">Alle Tracks ansehen</a> | <a href="/submit">Noch einen einreichen</a></p>
        '''

    return '''
    <h1 style="text-align:center;">Track einreichen</h1>
    <form method="post" style="text-align:center; margin-top:50px; font-size:18px;">
        <p>Name/Künstlername:<br><input type="text" name="name" required style="width:80%; max-width:400px; padding:10px;"></p>
        <p>Alter:<br><input type="number" name="alter" required style="width:80%; max-width:400px; padding:10px;"></p>
        <p>Track-Link (SoundCloud/YouTube):<br><input type="text" name="link" required style="width:80%; max-width:400px; padding:10px;"></p>
        <p><input type="submit" value="Einreichen" style="padding:15px 40px; font-size:18px; background:#ff4d4d; color:white; border:none; border-radius:10px;"></p>
    </form>
    <p style="text-align:center; margin-top:50px;"><a href="/">← Zurück</a></p>
    '''

@app.route('/tracks')
def alle_tracks():
    if not tracks:
        return '<h2 style="text-align:center;">Noch keine Tracks eingereicht</h2><p style="text-align:center;"><a href="/submit">Jetzt einer sein!</a></p>'
    
    liste = "<h1 style='text-align:center;'>Eingereichte Tracks</h1><ol style='max-width:600px; margin:40px auto; font-size:18px;'>"
    for t in tracks:
        liste += f"<li><b>{t['name']}</b> ({t['alter']} Jahre{t['bonus']})<br><a href='{t['link']}' target='_blank'>Track anhören</a><br><small>{t['datum']}</small></li><hr>"
    liste += "</ol><p style='text-align:center;'><a href='/submit'>Weiteren einreichen</a></p>"
    return liste

if __name__ == '__main__':
    app.run(debug=True)
