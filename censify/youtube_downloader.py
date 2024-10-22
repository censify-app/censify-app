import yt_dlp
import os
from youtubesearchpython import VideosSearch

class YouTubeDownloader:
    @staticmethod
    def download_from_url(video_url: str, output_dir: str = None) -> str:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s' if not output_dir else os.path.join(output_dir, '%(title)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit('.', 1)[0] + '.wav'
            return filename

    @staticmethod
    def search_videos(query: str, limit: int = 5) -> list:
        search = VideosSearch(query, limit=limit)
        results = search.result()
        return results['result']