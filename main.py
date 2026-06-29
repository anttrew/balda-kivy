from __future__ import annotations

import random
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from balda.dictionary import WordDictionary, normalize_word
from balda.engine import BaldaEngine
from balda.models import GameState
from balda.storage import Storage


WHITE = (1, 1, 1, 1)
LIGHT_GRAY = (0.86, 0.86, 0.86, 1)
MID_GRAY = (0.72, 0.72, 0.72, 1)
DARK_GRAY = (0.34, 0.34, 0.34, 1)
TEXT = (0.08, 0.08, 0.08, 1)
ERROR = (0.55, 0.05, 0.05, 1)
OK = (0.05, 0.35, 0.08, 1)


class RoundedButton(Button):
    bg_color = ListProperty([0.93, 0.93, 0.93, 1])
    radius = NumericProperty(dp(18))

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", TEXT)
        kwargs.setdefault("italic", True)
        kwargs.setdefault("font_size", "18sp")
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update_canvas, size=self._update_canvas, bg_color=self._update_canvas, radius=self._update_canvas)

    def _update_canvas(self, *_):
        self._color.rgba = self.bg_color
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._rect.radius = [self.radius]


class RootScreen(Screen):
    def app(self) -> "BaldaApp":
        return App.get_running_app()  # type: ignore[return-value]

    def make_title(self, text: str) -> Label:
        return Label(text=text, color=TEXT, font_size="28sp", italic=True, size_hint_y=None, height=dp(60))

    def show_message(self, text: str, error: bool = False) -> None:
        popup = Popup(
            title="Сообщение",
            title_align="center",
            content=Label(text=text, color=ERROR if error else TEXT, halign="center"),
            size_hint=(0.86, 0.36),
        )
        popup.open()


class MainMenuScreen(RootScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.continue_button: RoundedButton | None = None

    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(18))
        root.add_widget(Label(text="Балда", color=TEXT, font_size="42sp", italic=True, size_hint_y=None, height=dp(90)))
        root.add_widget(Label(text="локальная игра для 2–4 игроков", color=TEXT, font_size="16sp", italic=True, size_hint_y=None, height=dp(36)))

        new_game = RoundedButton(text="Начать новую игру", size_hint_y=None, height=dp(58))
        new_game.bind(on_release=lambda *_: setattr(self.manager, "current", "setup"))
        root.add_widget(new_game)

        self.continue_button = RoundedButton(text="Продолжить игру", size_hint_y=None, height=dp(58))
        self.continue_button.disabled = not self.app().storage.has_save()
        self.continue_button.opacity = 1 if not self.continue_button.disabled else 0.45
        self.continue_button.bind(on_release=self.continue_game)
        root.add_widget(self.continue_button)

        settings = RoundedButton(text="Настройки", size_hint_y=None, height=dp(58))
        settings.bind(on_release=lambda *_: setattr(self.manager, "current", "settings"))
        root.add_widget(settings)

        root.add_widget(Label(text="", size_hint_y=1))
        self.add_widget(root)

    def continue_game(self, *_):
        if self.app().load_saved_game():
            self.manager.current = "game"
        else:
            self.show_message("Сохранение не найдено или повреждено", error=True)


class SetupScreen(RootScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_spinner: Spinner | None = None
        self.players_spinner: Spinner | None = None
        self.name_inputs: list[TextInput] = []
        self.start_word_input: TextInput | None = None

    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10))
        root.add_widget(self.make_title("Новая игра"))

        row1 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        row1.add_widget(Label(text="Размер поля", color=TEXT, italic=True))
        self.size_spinner = Spinner(text="5", values=("5", "7"), italic=True)
        self.size_spinner.bind(text=lambda *_: self.update_start_hint())
        row1.add_widget(self.size_spinner)
        row1.add_widget(Label(text="Игроков", color=TEXT, italic=True))
        self.players_spinner = Spinner(text="2", values=("2", "3", "4"), italic=True)
        row1.add_widget(self.players_spinner)
        root.add_widget(row1)

        self.name_inputs = []
        for i in range(4):
            item = TextInput(
                text=f"Игрок {i + 1}",
                multiline=False,
                hint_text=f"Имя игрока {i + 1}",
                italic=True,
                size_hint_y=None,
                height=dp(44),
            )
            self.name_inputs.append(item)
            root.add_widget(item)

        self.start_word_input = TextInput(
            text="БАЛДА",
            multiline=False,
            hint_text="Стартовое слово по длине поля",
            italic=True,
            size_hint_y=None,
            height=dp(46),
        )
        root.add_widget(self.start_word_input)

        random_word = RoundedButton(text="Случайное стартовое слово", size_hint_y=None, height=dp(50))
        random_word.bind(on_release=lambda *_: self.pick_random_start_word())
        root.add_widget(random_word)

        start = RoundedButton(text="Старт", size_hint_y=None, height=dp(58))
        start.bind(on_release=lambda *_: self.start_game())
        root.add_widget(start)

        back = RoundedButton(text="Назад", bg_color=[0.96, 0.96, 0.96, 1], size_hint_y=None, height=dp(50))
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "menu"))
        root.add_widget(back)
        self.add_widget(root)

    def update_start_hint(self):
        if not self.size_spinner or not self.start_word_input:
            return
        size = int(self.size_spinner.text)
        current = normalize_word(self.start_word_input.text)
        if len(current) != size:
            words = self.app().dictionary.words_of_length(size)
            self.start_word_input.text = words[0] if words else ""
        self.start_word_input.hint_text = f"Стартовое слово из {size} букв"

    def pick_random_start_word(self):
        size = int(self.size_spinner.text if self.size_spinner else "5")
        words = self.app().dictionary.words_of_length(size)
        if not words:
            self.show_message(f"В словаре нет слов длиной {size}. Можно вписать своё.", error=True)
            return
        self.start_word_input.text = random.choice(words)

    def start_game(self):
        assert self.size_spinner and self.players_spinner and self.start_word_input
        size = int(self.size_spinner.text)
        count = int(self.players_spinner.text)
        names = [item.text.strip() or f"Игрок {i + 1}" for i, item in enumerate(self.name_inputs[:count])]
        initial_word = normalize_word(self.start_word_input.text)
        if len(initial_word) != size:
            self.show_message(f"Стартовое слово должно быть длиной {size} букв", error=True)
            return
        try:
            settings = self.app().settings_data
            state = GameState.new(
                size=size,
                player_names=names,
                initial_word=initial_word,
                strict_dictionary=bool(settings.get("strict_dictionary", False)),
                min_word_length=int(settings.get("min_word_length", 2)),
            )
        except ValueError as exc:
            self.show_message(str(exc), error=True)
            return
        self.app().set_game(state)
        self.manager.current = "game"


class SettingsScreen(RootScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strict_toggle: ToggleButton | None = None
        self.min_input: TextInput | None = None

    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        self.clear_widgets()
        settings = self.app().settings_data
        root = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(14))
        root.add_widget(self.make_title("Настройки"))

        self.strict_toggle = ToggleButton(
            text="Строгая проверка словаря: ВКЛ" if settings.get("strict_dictionary") else "Строгая проверка словаря: ВЫКЛ",
            state="down" if settings.get("strict_dictionary") else "normal",
            italic=True,
            size_hint_y=None,
            height=dp(54),
        )
        self.strict_toggle.bind(on_release=self.update_toggle_text)
        root.add_widget(self.strict_toggle)

        root.add_widget(Label(
            text="Если строгая проверка выключена, приложение запрещает только повторы.\nЕсли включена — слово должно быть в data/words_ru.txt.",
            color=TEXT,
            italic=True,
            halign="center",
            size_hint_y=None,
            height=dp(72),
        ))

        self.min_input = TextInput(
            text=str(settings.get("min_word_length", 2)),
            hint_text="Минимальная длина слова",
            multiline=False,
            input_filter="int",
            italic=True,
            size_hint_y=None,
            height=dp(46),
        )
        root.add_widget(self.min_input)

        save = RoundedButton(text="Сохранить настройки", size_hint_y=None, height=dp(56))
        save.bind(on_release=lambda *_: self.save_settings())
        root.add_widget(save)

        back = RoundedButton(text="Назад", bg_color=[0.96, 0.96, 0.96, 1], size_hint_y=None, height=dp(52))
        back.bind(on_release=lambda *_: setattr(self.manager, "current", "menu"))
        root.add_widget(back)
        root.add_widget(Label(text="", size_hint_y=1))
        self.add_widget(root)

    def update_toggle_text(self, *_):
        if self.strict_toggle:
            self.strict_toggle.text = "Строгая проверка словаря: ВКЛ" if self.strict_toggle.state == "down" else "Строгая проверка словаря: ВЫКЛ"

    def save_settings(self):
        assert self.strict_toggle and self.min_input
        min_len = int(self.min_input.text or "2")
        min_len = max(2, min(12, min_len))
        self.app().settings_data = {
            "strict_dictionary": self.strict_toggle.state == "down",
            "min_word_length": min_len,
        }
        self.app().storage.save_settings(self.app().settings_data)
        if self.app().state:
            self.app().state.strict_dictionary = self.app().settings_data["strict_dictionary"]
            self.app().state.min_word_length = self.app().settings_data["min_word_length"]
            self.app().save_game()
        self.show_message("Настройки сохранены")


class CellButton(Button):
    row = NumericProperty(0)
    col = NumericProperty(0)

    def __init__(self, row: int, col: int, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.background_normal = ""
        self.background_down = ""
        self.font_size = "24sp"
        self.bold = True
        self.color = TEXT


class GameScreen(RootScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status_label: Label | None = None
        self.word_label: Label | None = None
        self.grid: GridLayout | None = None
        self.words_box: BoxLayout | None = None
        self.cell_buttons: dict[tuple[int, int], CellButton] = {}
        self.last_message = ""
        self.last_message_error = False

    def on_pre_enter(self, *_):
        self.build()
        Clock.schedule_once(lambda *_: self.refresh(), 0)

    def engine(self) -> BaldaEngine:
        return self.app().engine

    def build(self):
        self.clear_widgets()
        state = self.app().state
        if state is None:
            self.add_widget(Label(text="Нет активной игры", color=TEXT))
            return

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        self.status_label = Label(text="", color=TEXT, italic=True, size_hint_y=None, height=dp(42))
        root.add_widget(self.status_label)

        self.grid = GridLayout(cols=state.size, rows=state.size, spacing=dp(3), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.cell_buttons.clear()
        for row in range(state.size):
            for col in range(state.size):
                button = CellButton(row=row, col=col, size_hint_y=None, height=dp(52))
                button.bind(on_release=self.on_cell_press)
                self.cell_buttons[(row, col)] = button
                self.grid.add_widget(button)
        root.add_widget(self.grid)

        self.word_label = Label(text="Слово: ", color=TEXT, font_size="20sp", italic=True, size_hint_y=None, height=dp(38))
        root.add_widget(self.word_label)

        controls1 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        submit = RoundedButton(text="Готово", font_size="15sp")
        submit.bind(on_release=lambda *_: self.submit_word())
        controls1.add_widget(submit)
        clear = RoundedButton(text="Очистить", font_size="15sp", bg_color=[0.96, 0.96, 0.96, 1])
        clear.bind(on_release=lambda *_: self.clear_selection())
        controls1.add_widget(clear)
        delete = RoundedButton(text="Удалить букву", font_size="15sp", bg_color=[0.96, 0.96, 0.96, 1])
        delete.bind(on_release=lambda *_: self.delete_pending())
        controls1.add_widget(delete)
        root.add_widget(controls1)

        controls2 = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        skip = RoundedButton(text="Пропустить", font_size="15sp", bg_color=[0.96, 0.96, 0.96, 1])
        skip.bind(on_release=lambda *_: self.skip_turn())
        controls2.add_widget(skip)
        finish = RoundedButton(text="Завершить", font_size="15sp", bg_color=[0.96, 0.96, 0.96, 1])
        finish.bind(on_release=lambda *_: self.finish_game())
        controls2.add_widget(finish)
        menu = RoundedButton(text="Меню", font_size="15sp", bg_color=[0.96, 0.96, 0.96, 1])
        menu.bind(on_release=lambda *_: setattr(self.manager, "current", "menu"))
        controls2.add_widget(menu)
        root.add_widget(controls2)

        root.add_widget(Label(text="Слова за игру", color=TEXT, italic=True, size_hint_y=None, height=dp(32)))
        scroll = ScrollView()
        self.words_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(4))
        self.words_box.bind(minimum_height=self.words_box.setter("height"))
        scroll.add_widget(self.words_box)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_cell_press(self, button: CellButton):
        state = self.app().state
        if not state or state.game_over:
            return
        cell = state.board[button.row][button.col]
        if cell.letter:
            result = self.engine().tap_letter_cell(button.row, button.col)
            self.set_status(result.message, not result.ok)
            self.refresh()
            return

        if state.pending_cell is not None:
            self.set_status("Сначала составьте слово или удалите новую букву", True)
            return
        if not self.engine().can_place_letter(button.row, button.col):
            self.set_status("Ставить букву можно только рядом с заполненной клеткой", True)
            return
        self.open_letter_popup(button.row, button.col)

    def open_letter_popup(self, row: int, col: int):
        layout = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        input_box = TextInput(multiline=False, hint_text="Одна буква", font_size="24sp", size_hint_y=None, height=dp(58))
        layout.add_widget(input_box)
        button = RoundedButton(text="Поставить", size_hint_y=None, height=dp(50))
        layout.add_widget(button)
        popup = Popup(title="Новая буква", content=layout, size_hint=(0.82, 0.34))

        def submit(*_):
            result = self.engine().place_letter(row, col, input_box.text)
            if result.ok:
                popup.dismiss()
                self.set_status(result.message)
                self.refresh()
                self.app().save_game()
            else:
                input_box.text = ""
                self.set_status(result.message, True)

        button.bind(on_release=submit)
        input_box.bind(on_text_validate=submit)
        popup.open()
        input_box.focus = True

    def submit_word(self):
        result = self.engine().submit_selected_word()
        self.set_status(result.message, not result.ok)
        if result.ok:
            self.app().save_game()
        self.refresh()
        if self.app().state and self.app().state.game_over:
            self.manager.current = "results"

    def clear_selection(self):
        self.engine().clear_selection()
        self.set_status("Выбор очищен")
        self.refresh()
        self.app().save_game()

    def delete_pending(self):
        result = self.engine().remove_pending_letter()
        self.set_status(result.message, not result.ok)
        if result.ok:
            self.app().save_game()
        self.refresh()

    def skip_turn(self):
        result = self.engine().skip_turn()
        self.set_status(result.message, not result.ok)
        if result.ok:
            self.app().save_game()
        self.refresh()

    def finish_game(self):
        if self.app().state:
            self.app().state.game_over = True
            self.app().save_game()
        self.manager.current = "results"

    def set_status(self, message: str, error: bool = False):
        self.last_message = message
        self.last_message_error = error
        if self.status_label and self.app().state:
            current = self.app().state.players[self.app().state.current_player]
            self.status_label.text = f"Ходит: {current.name} • очки: {current.score}\n{message}"
            self.status_label.color = ERROR if error else OK

    def refresh(self):
        state = self.app().state
        if not state:
            return
        if self.status_label:
            current = state.players[state.current_player]
            prefix = f"Ходит: {current.name} • очки: {current.score}"
            if self.last_message:
                self.status_label.text = f"{prefix}\n{self.last_message}"
                self.status_label.color = ERROR if self.last_message_error else OK
            else:
                self.status_label.text = prefix
                self.status_label.color = TEXT

        selected = set(state.selected_path)
        for (row, col), button in self.cell_buttons.items():
            cell = state.board[row][col]
            button.text = cell.letter
            button.color = TEXT
            if (row, col) in selected and cell.letter:
                button.background_color = MID_GRAY
            elif cell.kind == "start":
                button.background_color = LIGHT_GRAY
            elif cell.kind == "pending":
                button.background_color = DARK_GRAY
                button.color = WHITE
            else:
                button.background_color = WHITE

        if self.word_label:
            word = self.engine().current_word()
            self.word_label.text = f"Слово: {word}" if word else "Слово: "

        if self.words_box:
            self.words_box.clear_widgets()
            for player in state.players:
                words = ", ".join(player.words) if player.words else "—"
                label = Label(
                    text=f"{player.name} ({player.score}): {words}",
                    color=TEXT,
                    italic=True,
                    halign="left",
                    valign="top",
                    size_hint_y=None,
                    height=dp(34 + 18 * max(0, len(words) // 34)),
                )
                label.bind(size=lambda widget, *_: setattr(widget, "text_size", (widget.width, None)))
                self.words_box.add_widget(label)


class ResultsScreen(RootScreen):
    def on_pre_enter(self, *_):
        self.build()

    def build(self):
        self.clear_widgets()
        state = self.app().state
        root = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(12))
        root.add_widget(self.make_title("Итоги"))
        if not state:
            root.add_widget(Label(text="Нет данных", color=TEXT))
            self.add_widget(root)
            return

        ranking = self.app().engine.ranking()
        medals = ["🥇", "🥈", "🥉"]
        for i, player in enumerate(ranking[:3]):
            root.add_widget(Label(
                text=f"{medals[i]} {i + 1} место: {player.name} — {player.score}",
                color=TEXT,
                italic=True,
                font_size="22sp" if i == 0 else "19sp",
                size_hint_y=None,
                height=dp(52),
            ))

        root.add_widget(Label(text="Все результаты", color=TEXT, italic=True, size_hint_y=None, height=dp(34)))
        for player in ranking:
            root.add_widget(Label(
                text=f"{player.name}: {player.score} очков, слов: {len(player.words)}",
                color=TEXT,
                italic=True,
                size_hint_y=None,
                height=dp(32),
            ))

        new_game = RoundedButton(text="Новая игра", size_hint_y=None, height=dp(56))
        new_game.bind(on_release=lambda *_: setattr(self.manager, "current", "setup"))
        root.add_widget(new_game)

        menu = RoundedButton(text="В меню", bg_color=[0.96, 0.96, 0.96, 1], size_hint_y=None, height=dp(52))
        menu.bind(on_release=lambda *_: setattr(self.manager, "current", "menu"))
        root.add_widget(menu)
        root.add_widget(Label(text="", size_hint_y=1))
        self.add_widget(root)


class BaldaApp(App):
    title = "Балда"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage: Storage | None = None
        self.settings_data: dict = {}
        self.dictionary: WordDictionary | None = None
        self.state: GameState | None = None
        self.engine: BaldaEngine | None = None

    def build(self):
        self.storage = Storage(self.user_data_dir)
        self.settings_data = self.storage.load_settings()
        data_path = Path(__file__).parent / "data" / "words_ru.txt"
        self.dictionary = WordDictionary(data_path)

        manager = ScreenManager(transition=FadeTransition())
        manager.add_widget(MainMenuScreen(name="menu"))
        manager.add_widget(SetupScreen(name="setup"))
        manager.add_widget(SettingsScreen(name="settings"))
        manager.add_widget(GameScreen(name="game"))
        manager.add_widget(ResultsScreen(name="results"))
        return manager

    def set_game(self, state: GameState) -> None:
        self.state = state
        self.engine = BaldaEngine(state, self.dictionary)
        self.save_game()

    def load_saved_game(self) -> bool:
        assert self.storage is not None
        state = self.storage.load_game()
        if state is None:
            return False
        self.state = state
        self.engine = BaldaEngine(state, self.dictionary)
        return True

    def save_game(self) -> None:
        if self.storage and self.state:
            self.storage.save_game(self.state)


if __name__ == "__main__":
    BaldaApp().run()
