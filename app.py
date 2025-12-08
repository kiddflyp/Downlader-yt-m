from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import platform

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
# Definimos dónde buscar el archivo de cookies
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('url')
    quality = request.form.get('quality', '192')

    if not video_url:
        return "Error: URL no válida", 400

    try:
        # Configuración para usar cookies
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'ffmpeg_location': BASE_DIR if platform.system() == 'Windows' else None,
            # ESTA LÍNEA ES LA CLAVE PARA SALTAR EL BLOQUEO:
            'cookiefile': COOKIES_FILE, 
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
            final_name = os.path.basename(mp3_filename)

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(mp3_filename):
                    os.remove(mp3_filename)
            except Exception as error:
                print(f"Error borrando: {error}")
            return response

        response = send_file(mp3_filename, as_attachment=True)
        response.headers["x-filename"] = final_name 
        return response

    except Exception as e:
        print(f"Error: {e}")
        return f"Error de YouTube (Bloqueo anti-bot): {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
