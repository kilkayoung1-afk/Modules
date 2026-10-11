# Skatchat.py — модуль скачивания видео для Heroku UserBot
# Author: @Kilka_Young

import os
import re
import asyncio
import tempfile
from pathlib import Path

import yt_dlp
from heroku import loader, utils  # стандартные импорты Heroku

TEMP_DIR = Path(tempfile.gettempdir()) / "ub_downloads"
TEMP_DIR.mkdir(exist_ok=True)

URL_REGEX = re.compile(r"https?://\S+")

YDL_OPTS = {
    "outtmpl": str(TEMP_DIR / "%(id)s.%(ext)s"),
    "format": "best[filesize<2G]/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "merge_output_format": "mp4",
    "retries": 3,
    "socket_timeout": 30,
}


def _extract(url: str) -> dict:
    """Синхронное скачивание через yt-dlp."""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if not os.path.exists(filepath):
            base = os.path.splitext(filepath)[0]
            for ext in (".mp4", ".mkv", ".webm", ".mp3", ".m4a"):
                if os.path.exists(base + ext):
                    filepath = base + ext
                    break
        return {
            "path": filepath,
            "title": info.get("title", "video"),
            "uploader": info.get("uploader", "") or info.get("channel", ""),
            "duration": info.get("duration", 0) or 0,
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url", url),
        }


async def download_media(url: str) -> dict:
    return await asyncio.get_event_loop().run_in_executor(None, _extract, url)


@loader.tds
class SkatchatMod(loader.Module):
    """Скачивание видео с YouTube, TikTok, Instagram и др."""

    strings = {"name": "Skatchat"}

    @loader.command(alias="dl")
    async def skatchat(self, message):
        """Скачать видео по ссылке. Использование: .skatchat <url> или реплай на сообщение с ссылкой"""
        args = utils.get_args_raw(message)
        url = None

        if args and URL_REGEX.search(args):
            url = URL_REGEX.search(args).group(0)
        elif message.is_reply:
            reply = await message.get_reply_message()
            if reply and reply.text:
                m = URL_REGEX.search(reply.text)
                if m:
                    url = m.group(0)

        if not url:
            await utils.answer(
                message,
                "❌ Укажи ссылку: <code>.skatchat https://...</code> или ответь командой на сообщение с ссылкой.",
            )
            return

        status = await utils.answer(message, "⏳ <b>Скачиваю...</b>")

        try:
            data = await download_media(url)
        except Exception as e:
            await utils.answer(status, f"❌ Ошибка: <code>{e}</code>")
            return

        path = data["path"]
        size = os.path.getsize(path)

        if size > 2 * 1024 * 1024 * 1024:
            await utils.answer(status, f"❌ Файл слишком большой: {size / 1024 / 1024:.1f} MB")
            os.remove(path)
            return

        await utils.answer(status, "📤 <b>Отправляю...</b>")

        caption = (
            f"🎬 <b>{data['title']}</b>\n"
            f"👤 {data['uploader']}\n"
            f"⏱ {data['duration']} сек\n"
            f"🔗 <a href='{data['webpage_url']}'>Источник</a>\n\n"
            f"⚡ by @Kilka_Young"
        )

        try:
            await message.client.send_file(
                message.chat_id,
                path,
                caption=caption,
                supports_streaming=True,
                reply_to=message.reply_to_msg_id,
                thumb=data.get("thumbnail"),
            )
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        try:
            await status.delete()
        except Exception:
            pass
