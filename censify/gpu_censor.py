import os
import subprocess
from .whisper_config import load_model, transcribe_audio
import torch

class GPUCensor:
    def __init__(self, model_name="base"):
        """
        Инициализация GPU-ускоренного цензора
        :param model_name: Название модели Whisper ('tiny', 'base', 'small', 'medium', 'large')
        """
        # Очищаем кэш CUDA перед загрузкой модели
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        self.model, self.device = load_model(model_name)
        
        # Оптимизации для GPU
        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            self.model = self.model.half()  # Используем half-precision
    
    def censor_audio(self, audio_file: str, censor_words: list[str], output_file: str,
                    use_beep: bool = False, beep_hertz: int = 1000) -> str:
        """
        Цензурирование аудио с использованием GPU для распознавания речи
        
        :param audio_file: Путь к входному аудио файлу
        :param censor_words: Список слов для цензуры
        :param output_file: Путь к выходному файлу
        :param use_beep: Использовать ли бип вместо тишины
        :param beep_hertz: Частота бипа в герцах
        :return: Путь к обработанному файлу
        """
        try:
            # Очищаем память GPU перед обработкой нового файла
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            # Транскрибируем аудио используя GPU
            print(f"Transcribing audio using {self.device.upper()}")
            result = transcribe_audio(self.model, audio_file, self.device)
            print("Transcription complete")
            
            # Создаем временный файл со словами для цензуры
            temp_swears = "temp_swears.txt"
            with open(temp_swears, "w", encoding="utf-8") as f:
                f.write("\n".join(censor_words))
            
            print("Running censorship process")
            # Используем monkeyplug для цензуры
            cmd = [
                'monkeyplug',
                '-i', audio_file,
                '-o', output_file,
                '-w', temp_swears,
            ]
            
            if use_beep:
                cmd.extend(['-b', 'true'])
                cmd.extend(['--beep-hertz', str(beep_hertz)])
            
            subprocess.run(cmd, check=True)
            print("Censorship complete")
            
            # Очищаем временный файл
            if os.path.exists(temp_swears):
                os.remove(temp_swears)
            
            return output_file
            
        except Exception as e:
            print(f"Error during censorship: {str(e)}")
            if os.path.exists(temp_swears):
                os.remove(temp_swears)
            raise e
        
        finally:
            # Очищаем память GPU после завершения
            if self.device == "cuda":
                torch.cuda.empty_cache()
