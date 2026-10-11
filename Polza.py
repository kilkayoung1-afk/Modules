# meta developer: @Kilka_Young
# meta name: Polza
# meta description: Триггеры с обязательной подпиской на @KILKATOP1
# meta version: 1.0.0
# scope: hikka_only
# scope: hikka_min 1.2.10

from .. import loader, utils
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
from telethon.tl.types import Message

import re


@loader.tds
class PolzaMod(loader.Module):
    """Модуль Polza — триггеры с обязательной подпиской на @KILKATOP1"""

    strings = {
        "name": "Polza",
        "subscribe": (
            "❌ <b>Для использования триггеров необходимо подписаться на канал</b>\n"
            "👉 @KILKATOP1"
        ),
        "created": "✅ <b>Триггер создан</b>\n\n<b>Слово:</b> <code>{}</code>\n<b>Ответ:</b> <code>{}</code>",
        "deleted": "🗑 <b>Триггер удалён:</b> <code>{}</code>",
        "not_found": "❌ <b>Триггер не найден:</b> <code>{}</code>",
        "no_triggers": "📭 <b>Триггеров пока нет.</b>",
        "list_header": "📋 <b>Список триггеров:</b>\n\n",
        "bad_format": "❌ <b>Неверный формат.</b>\nИспользуй: <code>.create слово | ответ</code>",
        "empty": "❌ <b>Слово и ответ не могут быть пустыми.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "subscription_channel",
                "@KILKATOP1",
                "Канал для обязательной подписки",
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self._triggers = self.db.get("Polza", "triggers", {})
        self._channel = None

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
        channel = await self._get_channel()
        if channel is None:
            return False
        try:
            await self.client(
                GetParticipantRequest(channel=channel, participant=user_id)
            )
            return True
        except UserNotParticipantError:
            return False
        except Exception:
            return False

    def _save(self):
        self.db.set("Polza", "triggers", self._triggers)

    @loader.command()
    async def create(self, message: Message):
        """<слово> | <ответ> — создать триггер"""
        args = utils.get_args_raw(message)
        if not args or "|" not in args:
            await utils.answer(message, self.strings("bad_format"))
            return

        trigger, response = map(str.strip, args.split("|", 1))
        if not trigger or not response:
            await utils.answer(message, self.strings("empty"))
            return

        self._triggers[trigger.lower()] = {"text": trigger, "response": response}
        self._save()
        await utils.answer(
            message, self.strings("created").format(trigger, response)
        )

    @loader.command()
    async def deltrigger(self, message: Message):
        """<слово> — удалить триггер"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("not_found").format(""))
            return

        key = args.strip().lower()
        if key in self._triggers:
            del self._triggers[key]
            self._save()
            await utils.answer(message, self.strings("deleted").format(args.strip()))
        else:
            await utils.answer(message, self.strings("not_found").format(args.strip()))

    @loader.command()
    async def triggers(self, message: Message):
        """— список всех триггеров"""
        if not self._triggers:
            await utils.answer(message, self.strings("no_triggers"))
            return

        text = self.strings("list_header")
        for t in self._triggers.values():
            text += f"• <code>{t['text']}</code> → <i>{t['response']}</i>\n"
        await utils.answer(message, text)

    @loader.command()
    async def polza(self, message: Message):
        """— проверить подписку"""
        if await self._is_subscribed(message.sender_id):
            await utils.answer(message, "✅ <b>Вы подписаны!</b> Триггеры работают.")
        else:
            await utils.answer(
                message,
                self.strings("subscribe").replace(
                    "@KILKATOP1", self.config["subscription_channel"]
                ),
            )

    @loader.watcher(only_messages=True, only_incoming=True)
    async def watcher(self, message: Message):
        if not isinstance(message, Message):
            return
        if not message.text:
            return

        # Проверяем подписку автора сообщения
        if not await self._is_subscribed(message.sender_id):
            return

        text_lower = message.text.lower().strip()

        for key, data in self._triggers.items():
            if key in text_lower:
                try:
                    await message.reply(data["response"])
                except Exception:
                    pass
                break
