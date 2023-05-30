import string

from nltk.stem.snowball import SnowballStemmer

from voices.config import settings


class ContentFilter:
    __slots__ = ("obscene_words", "stemmer")

    def __init__(self) -> None:
        self.obscene_words = self.__load_words()
        self.stemmer = SnowballStemmer("russian")

    def normalize_text_words(self):
        with open(settings.RAW_OBSCENE_WORDS_FILE, encoding=settings.FILE_ENCODING) as file:
            obscene_words = {self.stemmer.stem(word.rstrip("\n")) for word in file}

        with open(settings.NORMALIZED_OBSCENE_WORDS_FILE, encoding=settings.FILE_ENCODING, mode="w+") as file:
            for word in obscene_words:
                file.write(f"{word}\n")

    @staticmethod
    def __load_words():
        try:
            with open(settings.NORMALIZED_OBSCENE_WORDS_FILE, encoding=settings.FILE_ENCODING) as file:
                obscene_words = {word.rstrip("\n") for word in file}
        except Exception:
            obscene_words = {}
        return obscene_words

    def is_obscene(self, text: str) -> bool:
        lowercase_text = text.lower()
        normalized_text = lowercase_text.translate(str.maketrans("", "", string.punctuation))

        for word in normalized_text.split(" "):
            normalized_word = self.stemmer.stem(word)
            if normalized_word in self.obscene_words:
                return True

        return False


content_filter = ContentFilter()
