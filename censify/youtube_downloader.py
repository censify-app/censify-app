import requests
import os
from config import Config
import logging

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.base_url = (f"{Config.YOUTUBE_PROXY_SERVER['protocol']}://"
                        f"{Config.YOUTUBE_PROXY_SERVER['host']}:"
                        f"{Config.YOUTUBE_PROXY_SERVER['port']}")

    def download_from_url(self, url: str, output_dir: str = '.') -> str:
        """Скачивает аудио с YouTube через прокси-сервер"""
        try:
            response = requests.post(
                f"{self.base_url}/download",
                data={'url': url},
                stream=True
            )

            if response.status_code != 200:
                raise Exception(f"Ошибка скачивания: {response.text}")

            # Получаем имя файла из заголовка
            filename = (response.headers.get('content-disposition') or 'audio.mp3')
            if 'filename=' in filename:
                filename = filename.split('filename=')[1].strip('"\'')
            output_path = os.path.join(output_dir, filename)

            # Сохраняем файл
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return output_path

        except Exception as e:
            logger.error(f"Ошибка при скачивании: {str(e)}")
            raise

    def search_videos(self, query: str, limit: int = 5) -> list:
        """Поиск видео на YouTube через прокси-сервер"""
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={
                    'query': query,
                    'limit': min(int(limit), 20)
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ошибка поиска: {response.text}")

            data = response.json()
            
            # Преобразуем результаты в формат, который ожидает фронтенд
            return [
                {
                    'title': video['title'],
                    'url': video['url'],
                    'thumbnail': video.get('thumbnail', ''),  # Может быть пустым
                    'duration': video['duration'],  # Уже в формате "M:SS"
                    'channel': video['channel'],
                    'channel_url': video.get('channel_url')  # Может быть None
                }
                for video in data['results']
            ]

        except Exception as e:
            logger.error(f"Ошибка при поиске видео: {str(e)}")
            return []