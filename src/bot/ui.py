"""Rendering helpers: every screen is a photo message whose image + caption is swapped in place."""
from __future__ import annotations

import asyncio
import logging

from telegram import InputMediaPhoto
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter, TelegramError

from src.utils.smallcaps import sc

log = logging.getLogger(__name__)
HTML = ParseMode.HTML
CAPTION_LIMIT = 1024


async def safe_edit_caption(bot, chat_id, mid, caption_html: str, kb=None) -> bool:
    """Edit caption (photo message) or text (text-only message). Never raises."""
    for _ in range(2):
        try:
            await bot.edit_message_caption(
                chat_id=chat_id, message_id=mid, caption=caption_html, parse_mode=HTML, reply_markup=kb
            )
            return True
        except RetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 0.5)
        except BadRequest as exc:
            msg = str(exc).lower()
            if "not modified" in msg:
                return True
            if "no caption" in msg:
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id, message_id=mid, text=caption_html, parse_mode=HTML, reply_markup=kb
                    )
                    return True
                except TelegramError:
                    return False
            return False
        except TelegramError:
            return False
    return False


async def _edit_media(bot, chat_id, mid, url, caption, kb) -> bool:
    for _ in range(2):
        try:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=mid,
                media=InputMediaPhoto(url, caption=caption, parse_mode=HTML),
                reply_markup=kb,
            )
            return True
        except RetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 0.5)
        except BadRequest as exc:
            if "not modified" in str(exc).lower():
                return True
            log.debug("edit_media failed: %s", exc)
            return False
        except TelegramError as exc:
            log.debug("edit_media failed: %s", exc)
            return False
    return False


async def _send(bot, chat_id, url, caption, kb, effect):
    attempts = [{"api_kwargs": {"message_effect_id": effect}}, {}] if effect else [{}]
    if url:
        for extra in attempts:
            try:
                m = await bot.send_photo(
                    chat_id, url, caption=caption, parse_mode=HTML, reply_markup=kb, **extra
                )
                return m.message_id
            except TelegramError as exc:
                log.debug("send_photo failed: %s", exc)
    for extra in attempts:
        try:
            m = await bot.send_message(chat_id, caption, parse_mode=HTML, reply_markup=kb, **extra)
            return m.message_id
        except TelegramError as exc:
            log.warning("send_message failed: %s", exc)
    return None


async def render(bot, images, chat_id, message_id, section, text, kb=None, effect=None):
    """Show `text` (+ anime image of `section`). Returns the id of the message now showing it."""
    caption = sc(text)
    url = await images.get(section) if len(caption) <= CAPTION_LIMIT else None

    if message_id is not None:
        if url:
            if await _edit_media(bot, chat_id, message_id, url, caption, kb):
                return message_id
        elif await safe_edit_caption(bot, chat_id, message_id, caption, kb):
            return message_id
        try:  # could not edit -> replace the old message
            await bot.delete_message(chat_id, message_id)
        except TelegramError:
            pass
    return await _send(bot, chat_id, url, caption, kb, effect)


async def reply_small(message, text: str, kb=None):
    """Small-caps reply to a user message (used for short errors/hints)."""
    try:
        return await message.reply_text(sc(text), parse_mode=HTML, reply_markup=kb)
    except TelegramError as exc:
        log.warning("reply failed: %s", exc)
        return None
