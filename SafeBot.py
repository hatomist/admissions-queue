import asyncio
import logging

from aiogram import Bot
from aiogram.utils import exceptions

from timer import Timer


class SafeBot(Bot):

    def _add_scheduler_tick(self, is_action: bool):
        if len(self._la1) >= self._reqs_per_second * 60:
            self._la1.pop(0)
        self._la1.append(is_action)
        if len(self._la5) >= self._reqs_per_second * 60 * 5:
            self._la5.pop(0)
        self._la5.append(is_action)
        if len(self._la15) >= self._reqs_per_second * 60 * 15:
            self._la15.pop(0)
        self._la15.append(is_action)

    def get_average_load(self):
        return {
            1: self._la1.count(True) / len(self._la1),
            5: self._la5.count(True) / len(self._la5),
            15: self._la15.count(True) / len(self._la15)
        }

    def __init__(self, token):
        self._events = []
        self._la1 = []
        self._la5 = []
        self._la15 = []
        self._reqs_per_second = 30

        async def event_scheduler():
            try:
                await self._events.pop(0)
                self._add_scheduler_tick(True)
            except IndexError:
                self._add_scheduler_tick(False)
            except Exception as e:
                self._add_scheduler_tick(True)
                logging.error('Exception in event scheduler:', e)

        async def report_la():
            la = self.get_average_load()
            logging.info(f'Load average: {la[1] * 100:.2f}% / 1m, {la[5] * 100:.2f}% / 5m, {la[15] * 100:.2f}% / 15m')

        self._scheduler = Timer(1 / self._reqs_per_second, event_scheduler, infinite=True, immediate=True)
        self._la_reporter = Timer(60, report_la, infinite=True)
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
