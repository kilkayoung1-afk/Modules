# meta developer: @Kilka_Young
# meta name: Polza
# meta description: Polza v2 — триггеры с медиа, кнопками, инлайн-меню, экспортом, ЧС и статистикой
# meta version: 2.0.0
# scope: hikka_only
# scope: hikka_min 1.2.10

import os
import io
import json
import random
import time
import re
import tempfile
from .. import loader, utils
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
from telethon.tl.types import Message
from telethon.tl.custom import Button


@loader.tds
class PolzaMod(loader.Module):
    """Polza v2 — триггеры с медиа, кнопками, меню, экспортом, ЧС и статистикой"""

    strings = {
        "name": "Polza",

        # ============ HELP ============
        "hello": (
            "😺😺😺😺😺\n\n"
            "🌘 <b>Polza v2</b>\n"
            "ℹ️ Модуль триггеров с обязательной подпиской\n\n"

            "<b>📌 Основные команды:</b>\n"
            "▫️ <code>.polzapanel</code> — инлайн-панель управления\n"
            "▫️ <code>.create слово | ответ</code> — создать триггер\n"
            "▫️ <code>.deltrigger слово</code> — удалить\n"
            "▫️ <code>.triggers</code> — список\n"
            "▫️ <code>.toptriggers</code> — топ\n"
            "▫️ <code>.polzastats</code> — статистика\n"
            "▫️ <code>.exportp</code> / <code>.importp</code> — экспорт/импорт\n"
            "▫️ <code>.polzablacklist</code> — ЧС чатов\n"
            "▫️ <code>.reloadbanner</code> — обновить баннер\n\n"

            "<b>🎲 Рандом:</b> <code>.create привет | Хай ;; Здарова ;; Ку</code>\n\n"

            "<b>📎 Медиа-триггер:</b>\n"
            "Ответь на стикер/гиф/фото и напиши:\n"
            "<code>.create кот | !media</code>\n\n"

            "<b>🔘 Кнопки в ответе:</b>\n"
            "<code>.create правила | Правила! [Правила|https://t.me/...]</code>\n\n"

            "<b>😀 Реакция вместо ответа:</b>\n"
            "<code>.create топ | 👍 -react</code>\n\n"

            "<b>🔤 Переменные:</b> {user} {name} {chat} {count}\n\n"

            "<b>🚩 Флаги:</b>\n"
            "• <code>-exact</code> — только точное совпадение\n"
            "• <code>-local</code> — только этот чат\n"
            "• <code>-cd N</code> — кулдаун N сек\n"
            "• <code>-admin</code> — только админы\n"
            "• <code>-react</code> — ответ как реакция\n\n"

            "——————\n"
            "⚠️ Нужна подписка на @KILKATOP1\n"
            "<b>Автор:</b> @Kilka_Young"
        ),

        "subscribe": (
            "❌ <b>Для использования триггеров нужно подписаться</b>\n👉 @KILKATOP1"
        ),
        "subscribed": "✅ <b>Вы подписаны!</b>",

        # ============ PANEL ============
        "panel_title": "🎛 <b>Polza — панель управления</b>\n\nВыбери действие:",

        # ============ CREATE ============
        "created": (
            "✅ <b>Триггер создан</b>\n\n"
            "<b>Слово:</b> <code>{}</code>\n"
            "<b>Ответ(ы):</b> <code>{}</code>\n"
            "<b>Режим:</b> {}\n\n{}"
        ),
        "created_media": (
            "✅ <b>Медиа-триггер создан</b>\n\n"
            "<b>Слово:</b> <code>{}</code>\n"
            "<b>Тип медиа:</b> {}\n\n{}"
        ),
        "bad_format": (
            "❌ <b>Неверный формат.</b>\n\n"
            "<code>.create слово | ответ</code>\n"
            "Медиа: ответь на стикер и напиши <code>.create слово | !media</code>\n\n"
            "Флаги: <code>-exact -local -cd N -admin -react</code>"
        ),
        "empty": "❌ <b>Пустое слово или ответ.</b>",
        "media_no_reply": (
            "❌ Чтобы создать медиа-триггер, ответь командой на стикер/гиф/фото."
        ),

        # ============ DELETE / LIST ============
        "deleted": "🗑 <b>Триггер удалён:</b> <code>{}</code>",
        "not_found": "❌ <b>Не найдено:</b> <code>{}</code>",
        "no_triggers": "📭 <b>Триггеров нет.</b>",
        "list_header": "📋 <b>Триггеры:</b>\n\n",
        "flags_help": (
            "🌐 глоб · 📍 лок · 🎯 точный · 🛡 админ · ⏳ cd · 📎 медиа · 😀 реакция"
        ),

        # ============ STATS ============
        "stats_header": "📊 <b>Статистика Polza</b>\n\n",
        "stats_body": (
            "🔢 Всего триггеров: <b>{}</b>\n"
            "🌐 Глобальных: <b>{}</b>\n"
            "📍 Локальных: <b>{}</b>\n"
            "📎 Медиа: <b>{}</b>\n"
            "⚡ Всего срабатываний: <b>{}</b>\n\n"
            "<b>🏆 Топ-5:</b>\n{}"
        ),

        # ============ BLACKLIST ============
        "bl_added": "🚫 <b>Чат добавлен в чёрный список.</b>\nТриггеры здесь больше не работают.",
        "bl_removed": "✅ <b>Чат удалён из ЧС.</b>",
        "bl_empty": "📭 Чёрный список пуст.",
        "bl_header": "🚫 <b>Чёрный список чатов:</b>\n\n",

        # ============ EXPORT / IMPORT ============
        "export_done": "📦 Экспорт готов. Триггеров: <b>{}</b>",
        "import_ok": "📥 Импортировано триггеров: <b>{}</b>",
        "import_bad": "❌ Файл повреждён или это не экспорт Polza.",

        # ============ BANNER ============
        "banner_ok": "✅ <b>Баннер обновлён.</b>",
        "banner_fail": "❌ <b>Не удалось скачать баннер.</b>",

        # ============ BUTTONS ============
        "btn_create": "➕ Создать",
        "btn_list": "📋 Список",
        "btn_top": "🏆 Топ",
        "btn_stats": "📊 Стата",
        "btn_export": "📦 Экспорт",
        "btn_close": "✖️ Закрыть",
        "btn_back": "◀️ Назад",
        "btn_reload": "🔄 Обновить",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("subscription_channel", "@KILKATOP1", "Канал подписки"),
            loader.ConfigValue("sub_cache_ttl", 300, "Кэш подписки (сек)"),
            loader.ConfigValue("default_cooldown", 3, "Кулдаун по умолчанию (сек)"),
            loader.ConfigValue("exact_match", False, "Глобально точное совпадение"),
            loader.ConfigValue("show_banner", True, "Показывать баннер"),
            loader.ConfigValue(
                "banner_url",
                "https://raw.githubusercontent.com/kilkayoung1-afk/Modules/main/dba85eea-4d86-4f4e-8672-7ffda3dd90ac.jpg",
                "Прямая ссылка на баннер",
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self._triggers = self.db.get("Polza", "triggers", {})
        self._counts = self.db.get("Polza", "counts", {})
        self._blacklist = self.db.get("Polza", "blacklist", [])
        self._cooldowns = {}
        self._sub_cache = {}
        self._channel = None
        self._banner_path = None
        self._media_cache = {}

        if self.config["show_banner"]:
            await self._download_banner()

    # ==================================================
    # ============ БАННЕР ============
    # ==================================================
    async def _download_banner(self, force: bool = False):
        url = (self.config["banner_url"] or "").strip()
        if not url:
            self._banner_path = None
            return

        cache_path = os.path.join(tempfile.gettempdir(), "polza_banner_cache")

        if not force and os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            if time.time() - os.path.getmtime(cache_path) < 7 * 24 * 3600:
                self._banner_path = cache_path
                return

        try:
            import aiohttp
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20),
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        self._banner_path = None
                        return
                    data = await resp.read()
                    if len(data) < 500:
                        self._banner_path = None
                        return
                    with open(cache_path, "wb") as f:
                        f.write(data)
                    self._banner_path = cache_path
        except Exception:
            self._banner_path = None

    async def _send_with_banner(self, message, text, buttons=None):
        if self.config["show_banner"] and not self._banner_path:
            await self._download_banner()

        if (
            self.config["show_banner"]
            and self._banner_path
            and os.path.exists(self._banner_path)
        ):
            try:
                await utils.answer(
                    message, text, file=self._banner_path, buttons=buttons
                )
                return
            except Exception:
                pass
        await utils.answer(message, text, buttons=buttons)

    # ==================================================
    # ============ ПОДПИСКА ============
    # ==================================================
    async def _get_channel(self):
        if self._channel is None:
            try:
                self._channel = await self.client.get_entity(
                    self.config["subscription_channel"]
                )
            except Exception:
                return None
        return self._channel

    async def _is_subscribed(self, user_id) -> bool:
        now = time.time()
        ttl = int(self.config["sub_cache_ttl"])

        cached = self._sub_cache.get(user_id)
        if cached and cached[1] > now:
            return cached[0]

        channel = await self._get_channel()
        if channel is None:
            return False

        try:
            await self.client(
                GetParticipantRequest(channel=channel, participant=user_id)
            )
            result = True
        except UserNotParticipantError:
            result = False
        except Exception:
            return False

        self._sub_cache[user_id] = (result, now + ttl)
        return result

    # ==================================================
    # ============ STORAGE ============
    # ==================================================
    def _save_triggers(self):
        self.db.set("Polza", "triggers", self._triggers)

    def _save_counts(self):
        self.db.set("Polza", "counts", self._counts)

    def _save_blacklist(self):
        self.db.set("Polza", "blacklist", self._blacklist)

    def _key(self, word: str, chat_id=None, local=False) -> str:
        w = word.lower().strip()
        return f"{chat_id}:{w}" if local else w

    # ==================================================
    # ============ RENDER VARIABLES ============
    # ==================================================
    async def _render(self, template: str, message, key: str) -> str:
        user = await message.get_sender()
        name = (getattr(user, "first_name", None) or "друг") if user else "друг"
        username = f"@{user.username}" if getattr(user, "username", None) else name
        count = self._counts.get(key, 0)
        chat = await message.get_chat()
        chat_title = getattr(chat, "title", "чат") or "чат"

        return (
            template
            .replace("{user}", username)
            .replace("{name}", name)
            .replace("{chat}", chat_title)
            .replace("{count}", str(count))
        )

    # ==================================================
    # ============ PARSE BUTTONS ============
    # ==================================================
    def _parse_buttons(self, text: str):
        pattern = re.compile(r"\[([^\|\]]+)\|([^\]]+)\]")
        buttons_data = pattern.findall(text)
        clean_text = pattern.sub("", text).strip()

        buttons = None
        if buttons_data:
            buttons = [
                [Button.url(name.strip(), url.strip())]
                for name, url in buttons_data
            ]
        return clean_text, buttons

    # ==================================================
    # ============ PANEL HELPERS ============
    # ==================================================
    def _panel_buttons(self):
        return [
            [
                Button.inline(self.strings("btn_create"), b"polza_create"),
                Button.inline(self.strings("btn_list"), b"polza_list"),
            ],
            [
                Button.inline(self.strings("btn_top"), b"polza_top"),
                Button.inline(self.strings("btn_stats"), b"polza_stats"),
            ],
            [
                Button.inline(self.strings("btn_export"), b"polza_export"),
                Button.inline(self.strings("btn_close"), b"polza_close"),
            ],
        ]

    def _back_buttons(self):
        return [[Button.inline(self.strings("btn_back"), b"polza_back")]]

    # ==================================================
    # ============ COMMAND: .polza ============
    # ==================================================
    @loader.command()
    async def polza(self, message: Message):
        """— справка + баннер + проверка подписки"""
        subscribed = await self._is_subscribed(message.sender_id)
        text = self.strings("hello")
        if subscribed:
            text += "\n\n" + self.strings("subscribed")
        else:
            text += "\n\n" + self.strings("subscribe").replace(
                "@KILKATOP1", self.config["subscription_channel"]
            )
        await self._send_with_banner(message, text)

    # ==================================================
    # ============ COMMAND: .polzapanel ============
    # ==================================================
    @loader.command()
    async def polzapanel(self, message: Message):
        """— инлайн-панель управления"""
        await self.inline.form(
            text=self.strings("panel_title"),
            message=message,
            reply_markup=self._panel_buttons(),
            ttl=180,
        )

    @loader.callback_handler()
    async def polza_cb(self, call):
        """Обработчик кнопок панели."""
        data = call.data.decode() if isinstance(call.data, bytes) else call.data

        # -------- Закрыть --------
        if data == "polza_close":
            try:
                await call.delete()
            except Exception:
                try:
                    await call.unload()
                except Exception:
                    pass
            return

        # -------- Назад --------
        if data == "polza_back":
            await call.edit(
                self.strings("panel_title"),
                reply_markup=self._panel_buttons(),
            )
            return

        # -------- Список --------
        if data == "polza_list":
            relevant = {
                k: v for k, v in self._triggers.items()
                if not v.get("local") or v.get("chat_id") == call.chat_id
            }
            if not relevant:
                text = self.strings("no_triggers")
            else:
                text = self.strings("list_header")
                for k, v in relevant.items():
                    count = self._counts.get(k, 0)
                    tag = "📍" if v.get("local") else "🌐"
                    if v.get("exact"):
                        tag += "🎯"
                    if v.get("admin_only"):
                        tag += "🛡"
                    if v.get("cooldown"):
                        tag += "⏳"
                    if v.get("media"):
                        tag += "📎"
                    if v.get("react"):
                        tag += "😀"
                    text += (
                        f"{tag} <code>{v['text']}</code> — "
                        f"<b>{count}</b>\n"
                    )
                text += "\n" + self.strings("flags_help")

            await call.edit(text, reply_markup=self._back_buttons())
            return

        # -------- Топ --------
        if data == "polza_top":
            if not self._counts:
                text = self.strings("no_triggers")
            else:
                sorted_items = sorted(
                    self._counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
                text = "🏆 <b>Топ триггеров:</b>\n\n"
                for i, (k, c) in enumerate(sorted_items, 1):
                    d = self._triggers.get(k)
                    if not d:
                        continue
                    text += f"{i}. <code>{d['text']}</code> — <b>{c}</b>\n"

            await call.edit(text, reply_markup=self._back_buttons())
            return

        # -------- Статистика --------
        if data == "polza_stats":
            total = len(self._triggers)
            glob = sum(1 for v in self._triggers.values() if not v.get("local"))
            loc = sum(1 for v in self._triggers.values() if v.get("local"))
            media = sum(1 for v in self._triggers.values() if v.get("media"))
            total_hits = sum(self._counts.values())

            top_lines = ""
            sorted_items = sorted(
                self._counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
            for i, (k, c) in enumerate(sorted_items, 1):
                d = self._triggers.get(k)
                if d:
                    top_lines += f"{i}. <code>{d['text']}</code> — <b>{c}</b>\n"
            if not top_lines:
                top_lines = "<i>нет данных</i>\n"

            text = self.strings("stats_header") + self.strings("stats_body").format(
                total, glob, loc, media, total_hits, top_lines
            )
            await call.edit(text, reply_markup=self._back_buttons())
            return

        # -------- Создать (подсказка) --------
        if data == "polza_create":
            text = (
                "➕ <b>Как создать триггер</b>\n\n"
                "Текстовый:\n"
                "<code>.create слово | ответ</code>\n\n"
                "С рандомом:\n"
                "<code>.create слово | отв1 ;; отв2</code>\n\n"
                "Медиа (ответь на стикер):\n"
                "<code>.create слово | !media</code>\n\n"
                "С кнопкой:\n"
                "<code>.create слово | текст [Кнопка|https://...]</code>\n\n"
                "С реакцией:\n"
                "<code>.create слово | 👍 -react</code>\n\n"
                "<b>Флаги:</b> <code>-exact -local -cd N -admin</code>"
            )
            await call.edit(text, reply_markup=self._back_buttons())
            return

        # -------- Экспорт --------
        if data == "polza_export":
            export_data = {
                "version": "2.0",
                "triggers": {
                    k: {**v, "media": None}
                    for k, v in self._triggers.items()
                },
                "counts": self._counts,
            }
            data_bytes = json.dumps(
                export_data, ensure_ascii=False, indent=2
            ).encode("utf-8")
            file = io.BytesIO(data_bytes)
            file.name = "polza_export.json"

            await call.answer(
                self.strings("export_done").format(len(self._triggers)),
                alert=True,
            )
            await self.client.send_file(
                call.chat_id,
                file,
                caption="📦 <b>Экспорт Polza</b>",
            )
            return

        await call.answer()

    # ==================================================
    # ============ COMMAND: .create ============
    # ==================================================
    @loader.command()
    async def create(self, message: Message):
        """<слово> | <ответ> [-exact] [-local] [-cd N] [-admin] [-react] — создать триггер"""
        args = utils.get_args_raw(message)
        if not args or "|" not in args:
            await utils.answer(message, self.strings("bad_format"))
            return

        trigger_part, rest = args.split("|", 1)

        flags = re.findall(r"-(exact|local|admin|react)\b", rest)
        cd_match = re.search(r"-cd\s+(\d+)", rest)

        response_raw = re.sub(r"-(exact|local|admin|react)\b", "", rest)
        response_raw = re.sub(r"-cd\s+\d+", "", response_raw).strip()

        trigger = trigger_part.strip()
        if not trigger:
            await utils.answer(message, self.strings("empty"))
            return

        is_media = response_raw.strip() == "!media"
        media_obj = None
        if is_media:
            reply = await message.get_reply_message()
            if not reply or not reply.media:
                await utils.answer(message, self.strings("media_no_reply"))
                return
            media_obj = reply.media

        if not is_media and not response_raw:
            await utils.answer(message, self.strings("empty"))
            return

        if is_media:
            responses = []
        else:
            responses = [r.strip() for r in response_raw.split(";;") if r.strip()]

        exact = "exact" in flags or bool(self.config["exact_match"])
        local = "local" in flags
        admin_only = "admin" in flags
        react = "react" in flags
        cooldown = int(cd_match.group(1)) if cd_match else int(self.config["default_cooldown"])

        chat_id = message.chat_id if local else None
        key = self._key(trigger, chat_id, local)

        self._triggers[key] = {
            "text": trigger,
            "responses": responses,
            "exact": exact,
            "local": local,
            "admin_only": admin_only,
            "react": react,
            "cooldown": cooldown,
            "chat_id": chat_id,
            "media": is_media,
        }

        if is_media:
            self._media_cache[key] = media_obj

        self._save_triggers()

        mode = "🎯 точное" if exact else "🔍 вхождение"

        flags_lines = []
        flags_lines.append(
            "🎯 Точное совпадение" if exact else "🔍 Вхождение в текст"
        )
        flags_lines.append(
            "📍 Только этот чат" if local else "🌐 Работает везде"
        )
        if admin_only:
            flags_lines.append("🛡 Только админы")
        if cooldown:
            flags_lines.append(f"⏳ Кулдаун {cooldown} сек")
        if react:
            flags_lines.append("😀 Ответ как реакция")
        if is_media:
            flags_lines.append("📎 Медиа-триггер")

        if is_media:
            await utils.answer(
                message,
                self.strings("created_media").format(
                    trigger,
                    media_obj.__class__.__name__,
                    "\n".join(flags_lines),
                ),
            )
        else:
            await utils.answer(
                message,
                self.strings("created").format(
                    trigger,
                    " ;; ".join(responses),
                    mode,
                    "\n".join(flags_lines),
                ),
            )

    # ==================================================
    # ============ COMMAND: .deltrigger ============
    # ==================================================
    @loader.command()
    async def deltrigger(self, message: Message):
        """<слово> — удалить триггер"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings("not_found").format(""))
            return

        candidates = [
            self._key(args, None, False),
            self._key(args, message.chat_id, True),
        ]
        removed = False
        for k in candidates:
            if k in self._triggers:
                del self._triggers[k]
                self._counts.pop(k, None)
                self._media_cache.pop(k, None)
                removed = True

        if removed:
            self._save_triggers()
            self._save_counts()
            await utils.answer(message, self.strings("deleted").format(args))
        else:
            await utils.answer(message, self.strings("not_found").format(args))

    # ==================================================
    # ============ COMMAND: .triggers ============
    # ==================================================
    @loader.command()
    async def triggers(self, message: Message):
        """— список триггеров"""
        relevant = {
            k: v for k, v in self._triggers.items()
            if not v.get("local") or v.get("chat_id") == message.chat_id
        }
        if not relevant:
            await utils.answer(message, self.strings("no_triggers"))
            return

        text = self.strings("list_header")
        for k, v in relevant.items():
            count = self._counts.get(k, 0)
            tag = "📍" if v.get("local") else "🌐"
            if v.get("exact"):
                tag += "🎯"
            if v.get("admin_only"):
                tag += "🛡"
            if v.get("cooldown"):
                tag += "⏳"
            if v.get("media"):
                tag += "📎"
            if v.get("react"):
                tag += "😀"
            preview = "📎 медиа" if v.get("media") else " ;; ".join(v["responses"])[:40]
            text += (
                f"{tag} <code>{v['text']}</code> → "
                f"<i>{preview}</i> 🔢 <b>{count}</b>\n"
            )
        text += "\n" + self.strings("flags_help")
        await utils.answer(message, text)

    # ==================================================
    # ============ COMMAND: .toptriggers ============
    # ==================================================
    @loader.command()
    async def toptriggers(self, message: Message):
        """— топ триггеров"""
        if not self._counts:
            await utils.answer(message, self.strings("no_triggers"))
            return

        sorted_items = sorted(
            self._counts.items(), key=lambda x: x[1], reverse=True
        )[:15]

        text = "🏆 <b>Топ триггеров:</b>\n\n"
        for i, (k, c) in enumerate(sorted_items, 1):
            data = self._triggers.get(k)
            if not data:
                continue
            text += f"{i}. <code>{data['text']}</code> — <b>{c}</b>\n"
        await utils.answer(message, text)

    # ==================================================
    # ============ COMMAND: .polzastats ============
    # ==================================================
    @loader.command()
    async def polzastats(self, message: Message):
        """— статистика модуля"""
        total = len(self._triggers)
        glob = sum(1 for v in self._triggers.values() if not v.get("local"))
        loc = sum(1 for v in self._triggers.values() if v.get("local"))
        media = sum(1 for v in self._triggers.values() if v.get("media"))
        total_hits = sum(self._counts.values())

        top_lines = ""
        sorted_items = sorted(
            self._counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
        for i, (k, c) in enumerate(sorted_items, 1):
            d = self._triggers.get(k)
            if d:
                top_lines += f"{i}. <code>{d['text']}</code> — <b>{c}</b>\n"
        if not top_lines:
            top_lines = "<i>нет данных</i>\n"

        text = self.strings("stats_header") + self.strings("stats_body").format(
            total, glob, loc, media, total_hits, top_lines
        )
        await utils.answer(message, text)

    # ==================================================
    # ============ COMMAND: .polzablacklist ============
    # ==================================================
    @loader.command()
    async def polzablacklist(self, message: Message):
        """— ЧС: add/del без аргумента — показать список"""
        args = utils.get_args_raw(message).strip().lower()

        if args in ("add", "+"):
            if message.chat_id not in self._blacklist:
                self._blacklist.append(message.chat_id)
                self._save_blacklist()
            await utils.answer(message, self.strings("bl_added"))
            return

        if args in ("del", "remove", "-"):
            if message.chat_id in self._blacklist:
                self._blacklist.remove(message.chat_id)
                self._save_blacklist()
            await utils.answer(message, self.strings("bl_removed"))
            return

        if not self._blacklist:
            await utils.answer(message, self.strings("bl_empty"))
            return

        text = self.strings("bl_header")
        for cid in self._blacklist:
            try:
                chat = await self.client.get_entity(cid)
                title = getattr(chat, "title", str(cid))
            except Exception:
                title = str(cid)
            text += f"• <code>{cid}</code> — <b>{title}</b>\n"

        text += "\n<i>.polzablacklist add — добавить этот чат\n.polzablacklist del — убрать</i>"
        await utils.answer(message, text)

    # ==================================================
    # ============ COMMAND: .exportp / .importp ============
    # ==================================================
    @loader.command()
    async def exportp(self, message: Message):
        """— экспорт всех триггеров в JSON"""
        export_data = {
            "version": "2.0",
            "triggers": {
                k: {**v, "media": None}
                for k, v in self._triggers.items()
            },
            "counts": self._counts,
        }
        data_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")
        file = io.BytesIO(data_bytes)
        file.name = "polza_export.json"

        await self.client.send_file(
            message.chat_id, file,
            caption=self.strings("export_done").format(len(self._triggers)),
            reply_to=message.id,
        )

    @loader.command()
    async def importp(self, message: Message):
        """— импорт триггеров (ответь на JSON-файл)"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, "❌ Ответь на JSON-файл экспорта.")
            return

        try:
            data = await reply.download_media(bytes)
            parsed = json.loads(data.decode("utf-8"))
        except Exception:
            await utils.answer(message, self.strings("import_bad"))
            return

        if "triggers" not in parsed:
            await utils.answer(message, self.strings("import_bad"))
            return

        count = 0
        for k, v in parsed["triggers"].items():
            v["media"] = False
            self._triggers[k] = v
            count += 1

        self._counts.update(parsed.get("counts", {}))
        self._save_triggers()
        self._save_counts()

        await utils.answer(message, self.strings("import_ok").format(count))

    # ==================================================
    # ============ COMMAND: .reloadbanner ============
    # ==================================================
    @loader.command()
    async def reloadbanner(self, message: Message):
        """— перекачать баннер"""
        cache_path = os.path.join(tempfile.gettempdir(), "polza_banner_cache")
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except Exception:
            pass
        self._banner_path = None
        await self._download_banner(force=True)
        if self._banner_path and os.path.exists(self._banner_path):
            await self._send_with_banner(message, self.strings("banner_ok"))
        else:
            await utils.answer(message, self.strings("banner_fail"))

    # ==================================================
    # ============ WATCHER ============
    # ==================================================
    @loader.watcher(only_messages=True, only_incoming=True)
    async def watcher(self, message: Message):
        if not isinstance(message, Message) or not message.text:
            return

        if message.chat_id in self._blacklist:
            return

        text = message.text
        text_lower = text.lower().strip()

        match_key = None
        for k, data in self._triggers.items():
            if data.get("local") and data.get("chat_id") != message.chat_id:
                continue

            trigger_text = data["text"].lower()
            if data.get("exact"):
                hit = (text_lower == trigger_text)
            else:
                hit = (trigger_text in text_lower)

            if hit:
                match_key = k
                break

        if not match_key:
            return

        data = self._triggers[match_key]

        if not await self._is_subscribed(message.sender_id):
            return

        if data.get("admin_only"):
            try:
                perms = await self.client.get_permissions(
                    message.chat_id, message.sender_id
                )
                if not (perms.is_admin or perms.is_creator):
                    return
            except Exception:
                return

        cd = int(data.get("cooldown") or 0)
        if cd > 0:
            now = time.time()
            last = self._cooldowns.get(match_key, 0)
            if now - last < cd:
                return
            self._cooldowns[match_key] = now

        self._counts[match_key] = self._counts.get(match_key, 0) + 1
        self._save_counts()

        # ============ МЕДИА ============
        if data.get("media"):
            media = self._media_cache.get(match_key)
            if media is None:
                return
            try:
                await self.client.send_file(
                    message.chat_id, media,
                    reply_to=message.id,
                )
            except Exception:
                pass
            return

        # ============ РЕАКЦИЯ ============
        if data.get("react"):
            reaction = data["responses"][0] if data["responses"] else "👍"
            try:
                await message.react(reaction)
            except Exception:
                pass
            return

        # ============ ОБЫЧНЫЙ ОТВЕТ ============
        response_template = random.choice(data["responses"])
        response_text = await self._render(response_template, message, match_key)

        clean_text, buttons = self._parse_buttons(response_text)

        try:
            await message.reply(clean_text, buttons=buttons, parse_mode="html")
        except Exception:
            try:
                await message.reply(clean_text)
            except Exception:
                pass
