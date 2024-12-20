import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

class ProfanityLoader:
    def __init__(self):
        self.languages_file = 'word_lists/languages/links.cfg'
        try:
            self.languages = self.load_language_links()
        except Exception as e:
            logger.error(f"Failed to load language links: {e}")
            self.languages = {}
        self.profanity_words = self.load_all_words()

    def load_language_links(self):
        try:
            with open(self.languages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Language links file not found: {self.languages_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in language links file: {e}")
            return {}

    def load_from_github(self, url: str) -> list[str]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return [word.strip() for word in response.text.split('\n') if word.strip()]
        except requests.RequestException as e:
            logger.error(f"Failed to load words from {url}: {e}")
            return []

    def load_all_words(self):
        all_words = set()
        
        # Загрузка слов из языковых списков
        for lang, url in self.languages.items():
            try:
                words = self.load_from_github(url)
                all_words.update(words)
                self.save_language_list(words, lang)
                logger.info(f"Loaded {len(words)} words for language {lang}")
            except Exception as e:
                logger.error(f"Failed to load words for language {lang}: {e}")
        
        # Загрузка слов из пользовательских списков
        try:
            custom_dir = 'word_lists/custom'
            if os.path.exists(custom_dir):
                for filename in os.listdir(custom_dir):
                    if filename.endswith('.txt'):
                        try:
                            with open(os.path.join(custom_dir, filename), 'r', encoding='utf-8') as f:
                                words = [word.strip() for word in f.readlines() if word.strip()]
                                all_words.update(words)
                                logger.info(f"Loaded {len(words)} words from {filename}")
                        except Exception as e:
                            logger.error(f"Failed to load words from {filename}: {e}")
        except Exception as e:
            logger.error(f"Failed to load custom words: {e}")
        
        logger.info(f"Total loaded words: {len(all_words)}")
        return list(all_words)

    def save_language_list(self, words: list[str], language: str):
        try:
            os.makedirs('word_lists/languages', exist_ok=True)
            with open(f'word_lists/languages/{language}.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(words))
            logger.info(f"Saved {len(words)} words for language {language}")
        except Exception as e:
            logger.error(f"Failed to save words for language {language}: {e}")

    def get_profanity_words(self):
        return self.profanity_words
