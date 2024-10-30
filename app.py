from flask import Flask, render_template, request, jsonify, send_file
from censify import YouTubeDownloader, Censor, ProfanityLoader
import os
import json

app = Flask(__name__)

# Создаем директорию для песен при запуске приложения
SONGS_DIR = os.path.join(os.path.dirname(__file__), 'songs')
os.makedirs(SONGS_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    downloader = YouTubeDownloader()
    
    try:
        results = downloader.search_videos(query, limit=5)
        # Добавляем URL превью к каждому результату
        for result in results:
            result['thumbnail'] = result['thumbnails'][0]['url']
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    video_url = data.get('video_url')
    custom_words = data.get('custom_words', [])
    use_beep = data.get('use_beep', True)
    beep_frequency = data.get('beep_frequency', 1000)
    
    try:
        downloader = YouTubeDownloader()
        censor = Censor()
        profanity_loader = ProfanityLoader()
        
        audio_file = downloader.download_from_url(video_url, output_dir=SONGS_DIR)
        
        censor_words = profanity_loader.get_profanity_words()
        if custom_words:
            censor_words.extend(custom_words)
            
        safe_filename = "".join(c for c in os.path.basename(audio_file) if c.isalnum() or c in (' ', '-', '_'))
        
        # Формируем префикс в зависимости от настроек цензуры
        prefix = 'cb{}_'.format(beep_frequency) if use_beep else 'cs_'
        output_file = os.path.join(SONGS_DIR, f"{prefix}{safe_filename}")
        if not output_file.lower().endswith('.mp3'):
            output_file += '.mp3'
            
        output_file = censor.censor_audio(
            audio_file,
            censor_words,
            output_file,
            use_beep=use_beep,
            beep_hertz=beep_frequency
        )
        
        # Удаляем исходный файл
        os.remove(audio_file)
        
        return jsonify({
            'success': True,
            'file': os.path.basename(output_file)  # Возвращаем только имя файла
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<path:filename>')
def download(filename):
    try:
        return send_file(
            os.path.join(SONGS_DIR, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
