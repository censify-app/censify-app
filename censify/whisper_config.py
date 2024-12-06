import torch
import whisper

def get_device():
    """Определяет доступное устройство для Whisper"""
    if torch.cuda.is_available():
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        return "cuda"
    else:
        print("GPU not available, using CPU")
        return "cpu"

def load_model(model_name="base"):
    """Загружает модель Whisper на нужное устройство"""
    device = get_device()
    print(f"Loading Whisper model '{model_name}' on {device}")
    model = whisper.load_model(model_name).to(device)
    return model, device

def transcribe_audio(model, audio_path, device):
    """Транскрибирует аудио используя указанное устройство"""
    # Используем half-precision для GPU для ускорения
    if device == "cuda":
        model = model.half()
    return model.transcribe(audio_path, fp16=(device == "cuda"))
