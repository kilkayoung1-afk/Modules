# Skatchat.py — модуль скачивания видео для Heroku UserBot
# Работает от имени пользователя (userbot) с поддержкой cookies
# Author: @Kilka_Young

import os
import re
import json
import asyncio
import logging
import tempfile
import subprocess
from pathlib import Path

import yt_dlp
from heroku import loader, utils

log = logging.getLogger(__name__)

# ==================== НАСТРОЙКИ ====================
TEMP_DIR = Path(tempfile.gettempdir()) / "ub_downloads"
TEMP_DIR.mkdir(exist_ok=True)

COOKIES_PATH = TEMP_DIR / "cookies.txt"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
URL_REGEX = re.compile(r"https?://\S+")


# ==================== БАЗОВЫЕ ОПЦИИ YT-DLP ====================
def _get_ydl_opts(quality: str = "best") -> dict:
    """Формирует опции для yt-dlp в зависимости от качества и наличия cookies."""
    # Универсальный селектор — не падает на любых видео
    format_map = {
        "best": "bestvideo*+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "480": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
        "audio": "bestaudio/best",
    }

    opts = {
        "outtmpl": str(TEMP_DIR / "%(id)s.%(ext)s"),
        "format": format_map.get(quality, format_map["best"]),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        "nocheckcertificate": True,
        "geo_bypass": True,
        # Имитация обычного пользователя (важно для YouTube)
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    # Если есть cookies — используем их (обход "bot check")
    if COOKIES_PATH.exists() and COOKIES_PATH.stat().st_size > 0:
        opts["cookiefile"] = str(COOKIES_PATH)

    return opts


# ==================== СКАЧИВАНИЕ ====================
def _extract(url: str, quality: str = "best") -> dict:
    """Синхронное скачивание через yt-dlp."""
    with yt_dlp.YoutubeDL(_get_ydl_opts(quality)) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

        # После merge формат может измениться (.webm → .mp4)
        if not os.path.exists(filepath):
            base = os.path.splitext(filepath)[0]
            for ext in (".mp4", ".mkv", ".webm", ".mp3", ".m4a"):
                if os.path.exists(base + ext):
                    filepath = base + ext
                    break

        return {
            "path": filepath,
            "title": info.get("title", "video"),
            "uploader": info.get("uploader") or info.get("channel", "") or "Unknown",
            "duration": info.get("duration", 0) or 0,
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url", url),
        }


async def download_media(url: str, quality: str = "best") -> dict:
    """Асинхронная обёртка над yt-dlp."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract, url, quality)


# ==================== МОДУЛЬ ====================
@loader.tds
class SkatchatMod(loader.Module):
    """Скачивание видео с YouTube, TikTok, Instagram, Twitter/X и др."""

    strings = {
        "name": "Skatchat",
        "no_url": (
            "❌ <b>Укажи ссылку:</b>\n"
            "<code>.skatchat https://...</code>\n\n"
            "Или ответь командой на сообщение со ссылкой."
        ),
        "downloading": "⏳ <b>Скачиваю...</b>",
        "sending": "📤 <b>Отправляю...</b>",
        "too_big": "❌ Файл слишком большой: {size:.1f} MB (лимит 2 GB)",
        "error": "❌ <b>Ошибка:</b>\n<code>{err}</code>",
        "cookies_set": "✅ Cookies успешно установлены ({size} байт)",
        "cookies_cleared": "🗑 Cookies удалены.",
        "cookies_missing": "❌ В ответе нет файла с cookies.",
        "help": (
            "📥 <b>Skatchat — Downloader by @Kilka_Young</b>\n\n"
            "<b>Команды:</b>\n"
            "• <code>.skatchat &lt;url&gt;</code> — скачать видео (best)\n"
            "• <code>.skatchat 720 &lt;url&gt;</code> — качество 720p\n"
            "• <code>.skatchat 480 &lt;url&gt;</code> — качество 480p\n"
            "• <code>.skatchat 360 &lt;url&gt;</code> — качество 360p\n"
            "• <code>.skatchat audio &lt;url&gt;</code> — только аудио (m4a)\n"
            "• <code>.skatchat</code> (реплаем на ссылку) — скачать из реплая\n\n"
            "<b>Cookies (для YouTube/TikTok/Instagram):</b>\n"
            "• Ответь <code>.skatchat cookies</code> на файл <code>cookies.txt</code>\n"
            "• <code>.skatchat clearcookies</code> — удалить cookies\n\n"
            "<b>Поддержка:</b> YouTube, TikTok, Instagram, Twitter/X, VK, Reddit, Twitch и др."
        ),
    }

    # ---------- основной обработчик ----------
    @loader.command(alias="dl", alias2="ск")
    async def skatchat(self, message):
        """Скачать видео. Использование: .skatchat [качество] <url>"""
        args = utils.get_args_raw(message) or ""
        args = args.strip()

        # --- обработка подкоманд для cookies ---
        low = args.lower()

        if low == "cookies":
            await self._set_cookies(message)
            return

        if low == "clearcookies":
            if COOKIES_PATH.exists():
                COOKIES_PATH.unlink()
            await utils.answer(message, self.strings["cookies_cleared"])
            return

        if not args or low in ("help", "помощь"):
            await utils.answer(message, self.strings["help"])
            return

        # --- парсим качество ---
        quality = "best"
        url = None

        parts = args.split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() in ("best", "720", "480", "360", "audio"):
            quality = parts[0].lower()
            m = URL_REGEX.search(parts[1])
            if m:
                url = m.group(0)
        else:
            m = URL_REGEX.search(args)
            if m:
                url = m.group(0)

        # --- если нет URL в аргументах — ищем в реплае ---
        if not url and message.is_reply:
            reply = await message.get_reply_message()
            if reply and reply.text:
                m = URL_REGEX.search(reply.text)
                if m:
                    url = m.group(0)

        if not url:
            await utils.answer(message, self.strings["no_url"])
            return

        status = await utils.answer(message, self.strings["downloading"])

        try:
            data = await download_media(url, quality)
        except Exception as e:
            log.exception("Ошибка скачивания")
            await utils.answer(status, self.strings["error"].format(err=str(e)[:500]))
            return

        path = data["path"]
        try:
            size = os.path.getsize(path)
        except OSError:
            await utils.answer(status, self.strings["error"].format(err="Файл не найден после скачивания"))
            return

        if size > MAX_FILE_SIZE:
            await utils.answer(status, self.strings["too_big"].format(size=size / 1024 / 1024))
            try:
                os.remove(path)
            except OSError:
                pass
            return

        await utils.answer(status, self.strings["sending"])

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
        except Exception as e:
            log.exception("Ошибка отправки")
            await utils.answer(status, self.strings["error"].format(err=str(e)[:500]))
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        try:
            await status.delete()
        except Exception:
            pass

    # ---------- установка cookies ----------
    async def _set_cookies(self, message):
        """Сохраняет cookies.txt, отправленный реплаем."""
        if not message.is_reply:
            await utils.answer(message, self.strings["cookies_missing"])
            return

        reply = await message.get_reply_message()
        if not reply or not reply.document:
            await utils.answer(message, self.strings["cookies_missing"])
            return

        status = await utils.answer(message, "⏳ Сохраняю cookies...")
        try:
            path = await reply.download_media(file=str(TEMP_DIR))
            with open(path, "rb") as f:
                content = f.read()

            # Проверка, что это похоже на cookies.txt
            if b"# Netscape HTTP Cookie File" not in content and b"youtube.com" not in content:
                await utils.answer(status, "⚠️ Файл не похож на cookies.txt (Netscape format).")
                os.remove(path)
                return

            with open(COOKIES_PATH, "wb") as f:
                f.write(content)

            if os.path.exists(path) and path != str(COOKIES_PATH):
                os.remove(path)

            await utils.answer(status, self.strings["cookies_set"].format(size=len(content)))
        except Exception as e:
            log.exception("Ошибка установки cookies")
            await utils.answer(status, self.strings["error"].format(err=str(e)[:300]))
