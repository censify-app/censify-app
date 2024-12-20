import os
import torch
from pathlib import Path

class Config:
    # Базовые настройки
    BASE_DIR = Path(__file__).parent
    SONGS_DIR = BASE_DIR / 'songs'
    
    # Настройки обработки аудио
    USE_GPU = False
    if USE_GPU:
        if torch.cuda.is_available():
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("GPU not available, using CPU")
    else:
        print("GPU not available, using CPU")
    
    # Настройки очереди задач
    TASK_QUEUE_WORKERS = 3  # Количество воркеров для обработки задач
    
    # Настройки Flask
    FLASK_DEBUG = False
    FLASK_PORT = 5000
    
    @classmethod
    def init_dirs(cls):
        """Инициализация необходимых директорий"""
        cls.SONGS_DIR.mkdir(exist_ok=True)