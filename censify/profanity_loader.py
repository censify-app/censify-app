import os
import json
import requests

class ProfanityLoader:
    def __init__(self):
        self.languages_file = 'word_lists/languages/links.cfg'
        self.languages = self.load_language_links()
        self.profanity_words = self.load_all_words()

    def load_language_links(self):
        with open(self.languages_file, 'r') as f:
            return json.load(f)

    def load_from_github(self, url: str) -> list[str]:
        response = requests.get(url)
        response.raise_for_status()
        return [word.strip() for word in response.text.split('\n') if word.strip()]

    def load_all_words(self):
        all_words = set()
        
        # Загрузка слов из языковых списков
        for lang, url in self.languages.items():
            words = self.load_from_github(url)
            all_words.update(words)
            self.save_language_list(words, lang)
        
        # Загрузка слов из пользовательских списков
        custom_dir = 'word_lists/custom'
        for filename in os.listdir(custom_dir):
            if filename.endswith('.txt'):
                with open(os.path.join(custom_dir, filename), 'r', encoding='utf-8') as f:
                    words = [word.strip() for word in f.readlines() if word.strip()]
                    all_words.update(words)
        
        return list(all_words)

    def save_language_list(self, words: list[str], language: str):
        os.makedirs('word_lists/languages', exist_ok=True)
        with open(f'word_lists/languages/{language}.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(words))

    def get_profanity_words(self):
        return self.profanity_words
