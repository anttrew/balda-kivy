from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import GameState


class Storage:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.save_path = self.directory / "savegame.json"
        self.settings_path = self.directory / "settings.json"

    def has_save(self) -> bool:
        return self.save_path.exists()

    def save_game(self, state: GameState) -> None:
        self.save_path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_game(self) -> GameState | None:
        if not self.save_path.exists():
            return None
        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
            return GameState.from_dict(data)
        except Exception:
            return None

    def delete_game(self) -> None:
        if self.save_path.exists():
            self.save_path.unlink()

    def save_settings(self, settings: dict[str, Any]) -> None:
        self.settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_settings(self) -> dict[str, Any]:
        defaults = {
            "strict_dictionary": False,
            "min_word_length": 2,
        }
        if not self.settings_path.exists():
            return defaults
        try:
            loaded = json.loads(self.settings_path.read_text(encoding="utf-8"))
            defaults.update(loaded)
        except Exception:
            pass
        return defaults
