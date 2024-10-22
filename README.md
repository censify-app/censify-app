# Censify

Web application for automatic censorship of profanity in audio files from YouTube.

## Features

- Search and download audio from YouTube
- Automatic profanity detection
- Two censorship modes: silence or beep
- Adjustable beep frequency (500-2000 Hz)
- Custom word list for censorship
- Processed files history
- Dark and light themes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sw1ftin/censify-app.git
cd censify-app
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate # For Linux/Mac
venv\Scripts\activate # For Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and go to `http://localhost:5000`

3. Enter song name or YouTube video URL

4. Configure censorship settings:
   - Add custom words for censorship
   - Choose censorship mode (silence/beep)
   - Adjust beep frequency if needed

5. Click "Process" and wait for completion

## Technologies

- Python (Flask)
- JavaScript
- MaterializeCSS
- yt-dlp
- monkeyplug

## Project Structure
```
censify-app/
├── app.py # Main application file
├── censify/ # Core module
├── static/
│ ├── css/ # Styles
│ └── js/ # JavaScript
├── templates/ # HTML templates
├── word_lists/ # Censorship word lists
└── requirements.txt # Dependencies
```

## License

MIT

## Author

Jakob Ornysh