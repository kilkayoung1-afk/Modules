from .. import loader, utils
from telethon.tl.functions.channels import GetParticipantRequest


@loader.tds
class TriggerMod(loader.Module):
    """Триггер с проверкой обязательной подписки."""

    strings = {
        "name": "Trigger",
        "subscribe": (
            "Для использования модуля подпишись на "
            "<a href='https://t.me/KILKATOP1'>@KILKATOP1</a>, "
            "затем повтори команду."
        ),
        "check_error": "Не удалось проверить подписку. Попробуй позже.",
        "done": "Триггер активирован.",
    }

    async def client_ready(self, client, db):
        self._client = client

    async def _is_subscribed(self):
        try:
            channel = await self._client.get_entity("@KILKATOP1")
            me = await self._client.get_me()
            await self._client(GetParticipantRequest(channel, me))
            return True
        except Exception:
            return False

    @loader.command()
    async def triggercmd(self, message):
        """Активировать триггер: .trigger [текст]"""
        try:
            subscribed = await self._is_subscribed()
        except Exception:
            return await utils.answer(message, self.strings["check_error"])

        if not subscribed:
            return await utils.answer(message, self.strings["subscribe"])

        text = utils.get_args_raw(message)
        await utils.answer(message, text or self.strings["done"])
)
            await utils.answer(status, self.strings["error"].format(err=str(e)[:300]))
