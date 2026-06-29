from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Cell:
    letter: str = ""
    kind: str = "empty"  # empty | start | normal | pending

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Cell":
        return cls(letter=data.get("letter", ""), kind=data.get("kind", "empty"))


@dataclass
class Player:
    name: str
    words: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(len(word) for word in self.words)

    def to_dict(self) -> dict:
        return {"name": self.name, "words": self.words}

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(name=data.get("name", "Игрок"), words=list(data.get("words", [])))


@dataclass
class GameState:
    size: int
    players: list[Player]
    board: list[list[Cell]]
    current_player: int = 0
    used_words: dict[str, str] = field(default_factory=dict)  # WORD -> player name
    pending_cell: Optional[tuple[int, int]] = None
    selected_path: list[tuple[int, int]] = field(default_factory=list)
    initial_word: str = ""
    strict_dictionary: bool = False
    min_word_length: int = 2
    game_over: bool = False

    @classmethod
    def new(
        cls,
        size: int,
        player_names: list[str],
        initial_word: str,
        strict_dictionary: bool = False,
        min_word_length: int = 2,
    ) -> "GameState":
        initial_word = initial_word.strip().upper().replace("Ё", "Ё")
        if len(initial_word) != size:
            raise ValueError(f"Стартовое слово должно содержать ровно {size} букв")

        board = [[Cell() for _ in range(size)] for _ in range(size)]
        middle = size // 2
        for col, letter in enumerate(initial_word):
            board[middle][col] = Cell(letter=letter, kind="start")

        players = [Player(name=name.strip() or f"Игрок {i + 1}") for i, name in enumerate(player_names)]
        return cls(
            size=size,
            players=players,
            board=board,
            initial_word=initial_word,
            strict_dictionary=strict_dictionary,
            min_word_length=min_word_length,
        )

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "players": [p.to_dict() for p in self.players],
            "board": [[cell.to_dict() for cell in row] for row in self.board],
            "current_player": self.current_player,
            "used_words": self.used_words,
            "pending_cell": list(self.pending_cell) if self.pending_cell else None,
            "selected_path": [list(item) for item in self.selected_path],
            "initial_word": self.initial_word,
            "strict_dictionary": self.strict_dictionary,
            "min_word_length": self.min_word_length,
            "game_over": self.game_over,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        pending = data.get("pending_cell")
        return cls(
            size=int(data["size"]),
            players=[Player.from_dict(item) for item in data.get("players", [])],
            board=[[Cell.from_dict(cell) for cell in row] for row in data.get("board", [])],
            current_player=int(data.get("current_player", 0)),
            used_words=dict(data.get("used_words", {})),
            pending_cell=tuple(pending) if pending else None,
            selected_path=[tuple(item) for item in data.get("selected_path", [])],
            initial_word=data.get("initial_word", ""),
            strict_dictionary=bool(data.get("strict_dictionary", False)),
            min_word_length=int(data.get("min_word_length", 2)),
            game_over=bool(data.get("game_over", False)),
        )
