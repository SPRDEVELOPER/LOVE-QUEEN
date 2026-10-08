"""Small-caps converter used for *every* piece of bot text and button label."""
import re

_SRC = "abcdefghijklmnopqrstuvwxyz"
_DST = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
assert len(_SRC) == len(_DST)
_TABLE = str.maketrans(dict(zip(_SRC, _DST)))

# html tags, html entities, urls, /commands and @mentions are left untouched
_KEEP = re.compile(r"(<[^>]*>|&[#\w]+;|https?://\S+|[/@][A-Za-z0-9_]+)")


def sc(text: str) -> str:
    parts = _KEEP.split(text)
    return "".join(p if i % 2 else p.lower().translate(_TABLE) for i, p in enumerate(parts))
