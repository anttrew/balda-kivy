from __future__ import annotations

from pathlib import Path


RUSSIAN_LETTERS = set("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")


def normalize_word(word: str) -> str:
    return "".join(ch for ch in word.strip().upper().replace("Ё", "Ё") if ch in RUSSIAN_LETTERS)


class WordDictionary:
    """Simple local word checker.

    The file format is intentionally boring: one Russian word per line, UTF-8.
    This class does not know morphology, so the file itself should already contain
    only allowed words if you want strict game validation.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.words: set[str] = set()
        self.reload()

    def reload(self) -> None:
        self.words.clear()
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                word = normalize_word(line)
                if word:
                    self.words.add(word)

    def has(self, word: str) -> bool:
        normalized = normalize_word(word)
        return normalized in self.words

    def words_of_length(self, length: int) -> list[str]:
        return sorted(word for word in self.words if len(word) == length)
