import random
import string

import pytest

from src.games.flames import FLAMES, calculate, cancel_common, eliminate, normalize


def test_same_names_always_valid_and_perfect_match():
    r = calculate("Surya", "Surya")
    assert r.remaining == 0 and r.letter == "M" and r.letter in FLAMES


def test_spaces_and_case_are_ignored():
    assert calculate("Mary Jane", "john").letter == calculate("maryjane", "JOHN").letter
    assert normalize("  A b-C!! 123 ") == "abc"


def test_repeated_letters_cancel_one_for_one():
    # aab vs ab -> one 'a' + one 'b' cancelled, one 'a' left
    _, _, remaining = cancel_common("aab", "ab")
    assert remaining == 1


def test_special_characters_are_stripped():
    assert calculate("j@hn!", "m#ary").letter == calculate("jhn", "mary").letter


def test_no_common_letters_known_answer():
    # john / mary: 8 letters remain -> hand-verified elimination ends on A
    r = calculate("john", "mary")
    assert r.remaining == 8 and r.letter == "A"


@pytest.mark.parametrize("count,expected", [(1, "S"), (2, "E")])
def test_known_counts(count, expected):
    assert eliminate(count)[0] == expected


def test_symmetric_and_deterministic():
    a, b = calculate("Surya", "Priya"), calculate("Priya", "Surya")
    assert a.letter == b.letter and a.percent == b.percent
    assert calculate("Surya", "Priya") == a


def test_steps_remove_exactly_five_letters():
    r = calculate("john", "mary")
    assert len(r.steps) == 5 and len(r.steps[-1].remaining) == 1


def test_percent_ranges():
    assert 0 <= calculate("john", "mary").percent <= 100


def test_empty_after_normalise_raises():
    with pytest.raises(ValueError):
        calculate("123", "abc")


def test_always_returns_flames_letter():
    rnd = random.Random(7)
    for _ in range(2000):
        a = "".join(rnd.choices(string.ascii_letters + " 1!", k=rnd.randint(1, 15)))
        b = "".join(rnd.choices(string.ascii_letters + " 1!", k=rnd.randint(1, 15)))
        if normalize(a) and normalize(b):
            assert calculate(a, b).letter in FLAMES
