from aiogram import types
from i18n import t


def divide_chunks(a, n):
    for i in range(0, len(a), n):
        yield a[i:i + n]


def get_geo_kbd(lang='ua'):
    return types.ReplyKeyboardMarkup(
        # aiogram requests lists instead of iterables as keyboard initializer, idk why
        one_time_keyboard=True,
        keyboard=[
            [
                types.KeyboardButton(t('SEND_POS_BTN', locale=lang), request_location=True)
            ]
        ],
        resize_keyboard=True
    )


# def get_reg_kbd(lang='ua'):
#     return types.InlineKeyboardMarkup(
#         row_width=1,
#         inline_keyboard=(
#             (
#                 types.InlineKeyboardButton(t('CERT_REG_BTN', locale=lang), callback_data='CertReg'),
#             ),
#             (
#                 types.InlineKeyboardButton(t('MANUAL_REG_BTN', locale=lang), callback_data='ManualReg'),
#             )
#         )
#     )


def get_menu_kbd(lang='ua', opt_reg_done: bool = False):
    if opt_reg_done:
        return types.InlineKeyboardMarkup(
            row_width=2,
            inline_keyboard=(
                (
                    types.InlineKeyboardButton(t('SHOW_ALL_QUEUES_BTN', locale=lang), callback_data='AllQueues'),
                    types.InlineKeyboardButton(t('SHOW_MY_QUEUES_BTN', locale=lang), callback_data='MyQueues'),
                ),
                (
                    types.InlineKeyboardButton(t('HELP_BTN', locale=lang), url=t('TELEGRAPH_URL', locale=lang)),
                    types.InlineKeyboardButton(t('TECHSUPPORT_BTN', locale=lang), url=t('LIVEGRAM_URL', locale=lang)),
                ),
                (
                    types.InlineKeyboardButton(t('CHANGE_DATA_BTN', locale=lang), callback_data='ChangeData'),
                )
            )
        )
    else:
        return types.InlineKeyboardMarkup(
            row_width=2,
            inline_keyboard=(
                (
                    types.InlineKeyboardButton(t('OPT_REGISTRATION_BTN', locale=lang), callback_data='OptReg'),
                ),
                (
                    types.InlineKeyboardButton(t('SHOW_ALL_QUEUES_BTN', locale=lang), callback_data='AllQueues'),
                    types.InlineKeyboardButton(t('SHOW_MY_QUEUES_BTN', locale=lang), callback_data='MyQueues'),
                ),
                (
                    types.InlineKeyboardButton(t('HELP_BTN', locale=lang), url=t('TELEGRAPH_URL', locale=lang)),
                    types.InlineKeyboardButton(t('TECHSUPPORT_BTN', locale=lang), url=t('LIVEGRAM_URL', locale=lang)),
                ),
                (
                    types.InlineKeyboardButton(t('CHANGE_DATA_BTN', locale=lang), callback_data='ChangeData'),
                )
            )
        )


def get_info_kbd(lang='ua'):
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('HELP_BTN', locale=lang), url=t('TELEGRAPH_URL', locale=lang)),
            ),
            (
                types.InlineKeyboardButton(t('TECHSUPPORT_BTN', locale=lang), url=t('LIVEGRAM_URL', locale=lang)),
            ),
        )
    )


def get_to_menu_kbd(lang='ua'):
    return types.InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('BACK_TO_MENU_BTN', locale=lang), callback_data='Menu'),
            ),
        )
    )


def get_queues_kbd(queues, my_queues=False, lang='ua'):
    queues = filter(lambda x: x['active'], queues)
    kbd = list(types.InlineKeyboardButton(queue['name'], callback_data=f'GetMyQueue{queue["id"]}'
                                                                       if my_queues else f'GetQueue{queue["id"]}')
               for queue in queues)
    return types.InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=list(divide_chunks(kbd, 2)) + [[types.InlineKeyboardButton(t('BACK_TO_MENU_BTN', locale=lang),
                                                                                   callback_data='Menu')]]
    )


def get_update_my_queue_kbd(queue_id, lang='ua'):
    return types.InlineKeyboardMarkup(
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('UPDATE_QUEUE_BTN', locale=lang), callback_data=f'GetMyQueue{queue_id}'),
            ),
            (
                types.InlineKeyboardButton(t('LEAVE_QUEUE_BTN', locale=lang), callback_data=f'LeaveQueue{queue_id}'),
            ),
            (
                types.InlineKeyboardButton(t('BACK_TO_MENU_BTN', locale=lang), callback_data='Menu'),
            )
        )
    )


def get_register_in_queue_kbd(queue_id, lang='ua'):
    return types.InlineKeyboardMarkup(
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('REGISTER_IN_QUEUE_BTN', locale=lang), callback_data=f'RegInQueue{queue_id}'),
            ),
            (
                types.InlineKeyboardButton(t('BACK_TO_MENU_BTN', locale=lang), callback_data='Menu'),
            )
        )
    )
