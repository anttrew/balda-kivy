from __future__ import annotations

from dataclasses import dataclass

from .dictionary import RUSSIAN_LETTERS, normalize_word, WordDictionary
from .models import GameState, Cell


@dataclass
class MoveResult:
    ok: bool
    message: str


class BaldaEngine:
    def __init__(self, state: GameState, dictionary: WordDictionary | None = None):
        self.state = state
        self.dictionary = dictionary

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.state.size and 0 <= col < self.state.size

    def cell(self, row: int, col: int) -> Cell:
        return self.state.board[row][col]

    def neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return [(r, c) for r, c in candidates if self.in_bounds(r, c)]

    def are_neighbors(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def can_place_letter(self, row: int, col: int) -> bool:
        if not self.in_bounds(row, col):
            return False
        if self.cell(row, col).letter:
            return False
        return any(self.cell(r, c).letter for r, c in self.neighbors(row, col))

    def place_letter(self, row: int, col: int, letter: str) -> MoveResult:
        if self.state.game_over:
            return MoveResult(False, "Игра уже завершена")
        if self.state.pending_cell is not None:
            return MoveResult(False, "Сначала составьте слово или удалите текущую букву")
        normalized = normalize_word(letter)
        if len(normalized) != 1 or normalized not in RUSSIAN_LETTERS:
            return MoveResult(False, "Введите одну русскую букву")
        if not self.can_place_letter(row, col):
            return MoveResult(False, "Букву можно ставить только рядом с уже заполненной клеткой")

        self.state.board[row][col] = Cell(letter=normalized, kind="pending")
        self.state.pending_cell = (row, col)
        self.state.selected_path = [(row, col)]
        return MoveResult(True, "Буква добавлена")

    def remove_pending_letter(self) -> MoveResult:
        if self.state.pending_cell is None:
            return MoveResult(False, "Новой буквы сейчас нет")
        row, col = self.state.pending_cell
        self.state.board[row][col] = Cell()
        self.state.pending_cell = None
        self.state.selected_path = []
        return MoveResult(True, "Буква удалена")

    def clear_selection(self) -> None:
        self.state.selected_path = []

    def tap_letter_cell(self, row: int, col: int) -> MoveResult:
        if not self.in_bounds(row, col):
            return MoveResult(False, "Клетка вне поля")
        if not self.cell(row, col).letter:
            return MoveResult(False, "Эта клетка пустая")

        pos = (row, col)
        path = self.state.selected_path

        if not path:
            self.state.selected_path = [pos]
            return MoveResult(True, self.current_word())

        if pos in path:
            index = path.index(pos)
            self.state.selected_path = path[: index + 1]
            return MoveResult(True, self.current_word())

        if self.are_neighbors(path[-1], pos):
            self.state.selected_path.append(pos)
            return MoveResult(True, self.current_word())

        self.state.selected_path = [pos]
        return MoveResult(True, self.current_word())

    def current_word(self) -> str:
        return "".join(self.cell(row, col).letter for row, col in self.state.selected_path)

    def validate_selected_word(self) -> MoveResult:
        word = normalize_word(self.current_word())
        if self.state.pending_cell is None:
            return MoveResult(False, "Сначала добавьте новую букву")
        if not word:
            return MoveResult(False, "Выберите буквы слова")
        if len(word) < self.state.min_word_length:
            return MoveResult(False, f"Слово должно быть не короче {self.state.min_word_length} букв")
        if self.state.pending_cell not in self.state.selected_path:
            return MoveResult(False, "Слово должно содержать новую букву")
        if len(set(self.state.selected_path)) != len(self.state.selected_path):
            return MoveResult(False, "Нельзя использовать одну клетку дважды")
        for left, right in zip(self.state.selected_path, self.state.selected_path[1:]):
            if not self.are_neighbors(left, right):
                return MoveResult(False, "Слово можно вести только по горизонтали и вертикали")
        if word in self.state.used_words:
            return MoveResult(False, f"Слово «{word}» уже было")
        if self.state.strict_dictionary:
            if self.dictionary is None or not self.dictionary.has(word):
                return MoveResult(False, f"Слова «{word}» нет в локальном словаре")
        return MoveResult(True, word)

    def submit_selected_word(self) -> MoveResult:
        validation = self.validate_selected_word()
        if not validation.ok:
            return validation

        word = normalize_word(self.current_word())
        player = self.state.players[self.state.current_player]
        player.words.append(word)
        self.state.used_words[word] = player.name

        if self.state.pending_cell:
            row, col = self.state.pending_cell
            self.state.board[row][col].kind = "normal"

        self.state.pending_cell = None
        self.state.selected_path = []
        self.state.current_player = (self.state.current_player + 1) % len(self.state.players)

        if self.is_board_full():
            self.state.game_over = True
            return MoveResult(True, "Поле заполнено. Игра завершена")
        return MoveResult(True, f"Слово «{word}» принято")

    def skip_turn(self) -> MoveResult:
        if self.state.pending_cell is not None:
            self.remove_pending_letter()
        self.state.selected_path = []
        self.state.current_player = (self.state.current_player + 1) % len(self.state.players)
        return MoveResult(True, "Ход пропущен")

    def is_board_full(self) -> bool:
        return all(cell.letter for row in self.state.board for cell in row)

    def ranking(self):
        return sorted(self.state.players, key=lambda player: player.score, reverse=True)
