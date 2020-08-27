import asyncio
import logging

from aiogram import Bot
from aiogram.utils import exceptions

from timer import Timer

import prometheus


class SafeBot(Bot):
    def __init__(self, token):
        self._events = []
        self._reqs_per_second = 30

        async def event_scheduler():
            try:
                await self._events.pop(0)
                prometheus.bot_requests_cnt.inc({})
            except IndexError:
                pass
            except exceptions.MessageNotModified:
                pass  # ignore, most probably because of queries
            except Exception as e:
                prometheus.bot_requests_cnt.inc({})
                logging.error(f'Exception in event scheduler: {e}')

        self._scheduler = Timer(1 / self._reqs_per_second, event_scheduler, infinite=True, immediate=True)
        super().__init__(token)

    async def edit_message_text(self, text,
                                chat_id=None,
                                message_id=None,
                                inline_message_id=None,
                                parse_mode=None,
                                disable_web_page_preview=None,
                                reply_markup=None):
        self._events.append(super(SafeBot, self).edit_message_text(text,
                                                                   chat_id,
                                                                   message_id,
                                                                   inline_message_id,
                                                                   parse_mode,
                                                                   disable_web_page_preview,
                                                                   reply_markup))

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None):
        self._events.append(self._send_message(chat_id, text, parse_mode, disable_web_page_preview,
                                               disable_notification, reply_to_message_id, reply_markup))

    async def _send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
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
