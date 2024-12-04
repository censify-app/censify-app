from flask import Flask, render_template, request, jsonify, send_file
from censify import YouTubeDownloader, Censor, ProfanityLoader
import os
import json
from task_queue import task_queue
import threading

app = Flask(__name__)

# Создаем директорию для песен при запуске приложения
SONGS_DIR = os.path.join(os.path.dirname(__file__), 'songs')
os.makedirs(SONGS_DIR, exist_ok=True)

def process_audio_task(video_url, custom_words, use_beep, beep_frequency, output_dir):
    """Функция обработки аудио для выполнения в отдельном потоке"""
    try:
        current_thread = threading.current_thread()
        
        # Инициализация компонентов
        downloader = YouTubeDownloader()
        censor = Censor()
        profanity_loader = ProfanityLoader()
        
        # Скачивание аудио
        task_queue.update_task_state(current_thread.task_id, 'DOWNLOADING')
        audio_file = downloader.download_from_url(video_url, output_dir=output_dir)
        
        # Загрузка слов для цензуры
        task_queue.update_task_state(current_thread.task_id, 'LOADING_WORDS')
        censor_words = profanity_loader.get_profanity_words()
        if custom_words:
            censor_words.extend(custom_words)
            
        # Формирование имени выходного файла
        safe_filename = "".join(c for c in os.path.basename(audio_file) if c.isalnum() or c in (' ', '-', '_'))
        prefix = 'cb{}_'.format(beep_frequency) if use_beep else 'cs_'
        output_file = os.path.join(output_dir, f"{prefix}{safe_filename}")
        if not output_file.lower().endswith('.mp3'):
            output_file += '.mp3'
            
        # Цензурирование аудио
        task_queue.update_task_state(current_thread.task_id, 'CENSORING')
        output_file = censor.censor_audio(
            audio_file,
            censor_words,
            output_file,
            use_beep=use_beep,
            beep_hertz=beep_frequency
        )
        
        # Очистка временных файлов
        task_queue.update_task_state(current_thread.task_id, 'CLEANING')
        os.remove(audio_file)
        
        return {
            'success': True,
            'file': os.path.basename(output_file)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

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
        # Добавляем задачу в очередь
        task_id = task_queue.add_task(
            process_audio_task,
            video_url,
            custom_words,
            use_beep,
            beep_frequency,
            SONGS_DIR
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    return jsonify(task_queue.get_task_status(task_id))

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
    app.run(debug=False, port=5000)
