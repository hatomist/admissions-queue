from aiogram import types
from i18n import t

import db


async def start_handler(message: types.Message):
    await message.reply(t('HELLO'))


async def query_handler(query: types.CallbackQuery):
    await query.answer(t('HELLO'))


def apply_handlers(dp):
    handlers = [
        {'fun': start_handler, 'named': {'commands': ['start']}},
    ]

    for handler in handlers:
        dp.register_message_handler(handler['fun'], **handler['named'])
    dp.register_callback_query_handler(query_handler)


