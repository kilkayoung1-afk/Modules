# meta developer: @Kilka_Young
# meta name: Polza
# meta description: Триггер Polza с обязательной подпиской на @KILKATOP1
# meta version: 1.0.0
# scope: hikka_only
# scope: hikka_min 1.2.10

from .. import loader, utils
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChannelPrivateError

@loader.tds
class PolzaMod(loader.Module):
    """Модуль Polza с обязательной подпиской на @KILKATOP1"""

    strings = {
        "name": "Polza",
        "subscribe": "❌ <b>Для использования модуля необходимо подписаться на канал</b> @KILKATOP1",
        "success": "✅ <b>Polza</b>\n\nВы подписаны! Триггер сработал.",
    }

    async def client_ready(self, client, db):
        self.client = client
        # Получаем сущность канала для проверки подписки
        self.channel = await self.client.get_entity("@KILKATOP1")

    async def _check_sub(self, user_id):
        """Проверяет, подписан ли пользователь на канал."""
        try:
            await self.client(GetParticipantRequest(
                channel=self.channel,
                participant=user_id
            ))
            return True
        except UserNotParticipantError:
            return False
        except ChannelPrivateError:
            return False
        except Exception:
            return False

    @loader.command()
    async def polza(self, message):
        """Триггер Polza (проверяет подписку)"""
        user_id = message.sender_id
        if not await self._check_sub(user_id):
            await utils.answer(message, self.strings("subscribe"))
            return
        await utils.answer(message, self.strings("success"))
