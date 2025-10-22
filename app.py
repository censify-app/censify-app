from flask import Flask, render_template, request, jsonify, send_file
from censify import YouTubeDownloader, Censor, ProfanityLoader, GPUCensor
from config import Config
from pathlib import Path
import json
from task_queue import task_queue
import threading
import hashlib
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_audio_task(source, custom_words, use_beep, beep_frequency, output_dir):
    """Функция обработки аудио для выполнения в отдельном потоке"""
    try:
        current_thread = threading.current_thread()
        logger.info(f"Starting audio processing task for {source}")
        
        # Инициализация компонентов
        downloader = YouTubeDownloader()
        censor = GPUCensor(model_name=Config.WHISPER_MODEL) if Config.USE_GPU else Censor()
        profanity_loader = ProfanityLoader()
        
        # Определяем, это URL или локальный файл
        source_path = Path(source)
        is_local_file = source_path.exists()
        logger.info(f"Source is {'local file' if is_local_file else 'URL'}")
        
        # Получаем аудио файл
        if is_local_file:
            audio_file = source_path
            task_queue.update_task_state(current_thread.task_id, 'PROCESSING')
            logger.info(f"Processing local file: {audio_file}")
        else:
            task_queue.update_task_state(current_thread.task_id, 'DOWNLOADING')
            audio_file = Path(downloader.download_from_url(source, output_dir=output_dir))
            logger.info(f"Downloaded file: {audio_file}")
        
        # Загрузка слов для цензуры
        task_queue.update_task_state(current_thread.task_id, 'LOADING_WORDS')
        censor_words = profanity_loader.get_profanity_words()
        if custom_words:
            censor_words.extend(custom_words)
        logger.info(f"Loaded {len(censor_words)} words for censorship")
        
        # Формирование имени выходного файла
        safe_filename = "".join(c for c in audio_file.stem if c.isalnum() or c in (' ', '-', '_'))
        
        params_str = f"{','.join(sorted(custom_words))}-{use_beep}-{beep_frequency}"
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        prefix = f"cb{beep_frequency}_" if use_beep else "cs_"
        output_file = Path(output_dir) / f"{prefix}{safe_filename}_{params_hash}"
        
        # Проверяем оба варианта имени файла (.mp3 и .mp3.mp3)
        existing_file = output_file.with_suffix('.mp3')
        existing_file_double = output_file.with_suffix('.mp3.mp3')
        
        if existing_file.exists():
            logger.info(f"Found existing processed file: {existing_file}")
            return {
                'success': True,
                'file': existing_file.name
            }
        elif existing_file_double.exists():
            logger.info(f"Found existing processed file: {existing_file_double}")
            return {
                'success': True,
                'file': existing_file_double.name
            }
        
        # Обработка аудио
        task_queue.update_task_state(current_thread.task_id, 'CENSORING')
        logger.info(f"Starting processing: {output_file}")
        
        # monkeyplug автоматически добавляет .mp3 к выходному файлу
        processed_path = censor.censor_audio(
            str(audio_file),
            censor_words,
            str(output_file),
            use_beep=use_beep,
            beep_hertz=beep_frequency
        )
        logger.info("Processing completed")
        
        # Проверяем оба варианта выходного файла
        censored_file = Path(processed_path)
        if not censored_file.exists():
            censored_file = censored_file.with_suffix(censored_file.suffix + '.mp3')
            
        if not censored_file.exists():
            raise Exception(f"Output file was not created: {censored_file}")
            
        logger.info(f"Successfully created output file: {censored_file}")
        
        # Очистка временных файлов
        task_queue.update_task_state(current_thread.task_id, 'CLEANING')
        if not is_local_file:
            audio_file.unlink()
            logger.info("Temporary files cleaned")
        
        return {
            'success': True,
            'file': censored_file.name
        }
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    downloader = YouTubeDownloader()
    
    try:
        results = downloader.search_videos(query, limit=5)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
            Config.SONGS_DIR
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

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        logger.error("No file in request")
        return jsonify({'success': False, 'error': 'No file uploaded'})
        
    file = request.files['file']
    if file.filename == '':
        logger.error("Empty filename")
        return jsonify({'success': False, 'error': 'No file selected'})
        
    if not Path(file.filename).suffix.lower() in ['.mp3', '.wav', '.m4a', '.ogg']:
        logger.error(f"Unsupported format: {file.filename}")
        return jsonify({'success': False, 'error': 'Unsupported file format'})
    
    try:
        # Сохраняем загруженный файл
        filename = secure_filename(file.filename)
        temp_path = Path(Config.SONGS_DIR) / f"temp_{filename}"
        file.save(str(temp_path))
        
        # Проверяем, что файл сохранился
        if not temp_path.exists():
            raise Exception("File was not saved")
        
        file_size = temp_path.stat().st_size
        logger.info(f"Saved file {temp_path} ({file_size} bytes)")
        
        if file_size == 0:
            raise Exception("Saved file is empty")
            
        # Получаем параметры цензуры
        custom_words = json.loads(request.form.get('custom_words', '[]'))
        use_beep = request.form.get('use_beep', 'true').lower() == 'true'
        beep_frequency = int(request.form.get('beep_frequency', 1000))
        
        # Добавляем задачу в очередь
        task_id = task_queue.add_task(
            process_audio_task,
            str(temp_path),
            custom_words,
            use_beep,
            beep_frequency,
            Config.SONGS_DIR
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'filename': filename
        })
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<path:filename>')
def download(filename):
    try:
        file_path = Path(Config.SONGS_DIR) / filename
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=Config.FLASK_DEBUG, port=Config.FLASK_PORT)
