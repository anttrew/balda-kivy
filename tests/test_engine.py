from balda.dictionary import WordDictionary
from balda.engine import BaldaEngine
from balda.models import GameState


class FakeDictionary:
    def __init__(self, words):
        self.words = set(words)

    def has(self, word):
        return word in self.words


def make_engine():
    state = GameState.new(
        size=5,
        player_names=["Аня", "Боря"],
        initial_word="БАЛДА",
        strict_dictionary=False,
    )
    return BaldaEngine(state, FakeDictionary({"БАЛДА", "ЛАД", "АД"}))


def test_place_letter_only_near_existing_cell():
    engine = make_engine()
    assert not engine.can_place_letter(0, 0)
    assert engine.can_place_letter(1, 0)


def test_submit_word_requires_pending_letter():
    engine = make_engine()
    assert engine.place_letter(1, 0, "А").ok
    # А (1,0) -> Б (2,0) -> А (2,1)
    engine.state.selected_path = [(1, 0), (2, 0), (2, 1)]
    result = engine.submit_selected_word()
    assert result.ok
    assert engine.state.players[0].score == 3


def test_duplicate_words_are_rejected():
    engine = make_engine()
    assert engine.place_letter(1, 0, "А").ok
    engine.state.selected_path = [(1, 0), (2, 0), (2, 1)]
    assert engine.submit_selected_word().ok

    assert engine.place_letter(3, 0, "А").ok
    engine.state.selected_path = [(3, 0), (2, 0), (2, 1)]
    result = engine.submit_selected_word()
    assert not result.ok
