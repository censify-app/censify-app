import subprocess
import os
import tempfile

class Censor:
    def censor_audio(self, audio_file: str, censor_words: list[str], output_file: str, 
                    use_beep: bool = False, 
                    beep_hertz: int = 1000,
                    pad_ms: int = 0,
                    pad_ms_pre: int = 0,
                    pad_ms_post: int = 0) -> str:
        """Цензурирование аудио с помощью monkeyplug
        
        Args:
            audio_file: Путь к входному аудио файлу
            censor_words: Список слов для цензуры
            output_file: Путь к выходному файлу
            use_beep: Использовать бип вместо тишины
            beep_hertz: Частота бипа в герцах
            pad_ms: Отступ в миллисекундах с обеих сторон
            pad_ms_pre: Отступ в миллисекундах перед цензурой
            pad_ms_post: Отступ в миллисекундах после цензуры
        """
        temp_swears = None
        try:
            if not output_file.lower().endswith('.mp3'):
                output_file = f"{output_file}.mp3"
                
            temp_swears = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            ascii_words = [word for word in censor_words if all(ord(c) < 128 for c in word)]
            temp_swears.write('\n'.join(ascii_words))
            temp_swears.flush()
            temp_swears.close()
            
            cmd = [
                'monkeyplug',
                '-i', audio_file,
                '-o', output_file,
                '-w', temp_swears.name,
            ]
            
            if use_beep:
                cmd.extend(['-b', 'true'])
                cmd.extend(['--beep-hertz', str(beep_hertz)])
            
            if pad_ms:
                cmd.extend(['--pad-milliseconds', str(pad_ms)])
            if pad_ms_pre:
                cmd.extend(['--pad-milliseconds-pre', str(pad_ms_pre)])
            if pad_ms_post:
                cmd.extend(['--pad-milliseconds-post', str(pad_ms_post)])
            
            subprocess.run(cmd, check=True)
            return output_file
            
        finally:
            if temp_swears and os.path.exists(temp_swears.name):
                os.remove(temp_swears.name)
