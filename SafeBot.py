import logging

from aiogram import Bot
from aiogram.utils import exceptions


class SafeBot(Bot):
    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None):
        log = logging.getLogger('bot')
        try:
            await super(SafeBot, self).send_message(chat_id, text, parse_mode, disable_web_page_preview,
                                                    disable_notification, reply_to_message_id, reply_markup)
        except exceptions.BotBlocked:
            log.error(f"Target [ID:{chat_id}]: blocked by user")
        except exceptions.ChatNotFound:
            log.error(f"Target [ID:{chat_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            log.error(f"Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return await self.send_message(chat_id, text, parse_mode, disable_web_page_preview,
                                           disable_notification, reply_to_message_id, reply_markup)  # Recursive call
        except exceptions.UserDeactivated:
            log.error(f"Target [ID:{chat_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            log.exception(f"Target [ID:{chat_id}]: failed")
        else:
            # log.info(f"Target [ID:{user_id}]: success")
            return True
        return False
