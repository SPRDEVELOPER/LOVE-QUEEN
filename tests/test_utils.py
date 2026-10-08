from src.utils.ratelimit import RateLimiter
from src.utils.smallcaps import sc
from src.utils.validators import validate_name


def test_smallcaps_basic_and_markup_preserved():
    assert sc("Hello") == "ʜᴇʟʟᴏ"
    assert sc("<b>flames</b> /start @bot_name &amp;") == "<b>ꜰʟᴀᴍᴇꜱ</b> /start @bot_name &amp;"


def test_smallcaps_keeps_emoji_and_digits():
    assert sc("🔥 25%") == "🔥 25%"


def test_validate_name():
    assert validate_name("", 30)[2] == "empty"
    assert validate_name("   ", 30)[2] == "empty"
    assert validate_name("12345", 30)[2] == "no_letters"
    assert validate_name("a" * 31, 30)[2] == "too_long"
    assert validate_name("  Sur  ya ", 30) == (True, "Sur ya", None)
    assert validate_name("சூர்யா", 30)[0] is True


def test_rate_limiter():
    rl = RateLimiter(3, 60)
    assert [rl.allow(1) for _ in range(4)] == [True, True, True, False]
    assert rl.allow(2)
