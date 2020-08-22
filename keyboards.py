from aiogram import types
from i18n import t


def get_geo_kbd(lang='ua'):
    return types.ReplyKeyboardMarkup(
        # aiogram requests lists instead of iterables as keyboard initializer, idk why
        one_time_keyboard=True,
        keyboard=[
            [
                types.KeyboardButton(t('SEND_POS_BTN', locale=lang), request_location=True)
            ]
        ]
    )


def get_reg_kbd(lang='ua'):
    return types.InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('CERT_REG_BTN', locale=lang), callback_data='CertReg'),
            ),
            (
                types.InlineKeyboardButton(t('MANUAL_REG_BTN', locale=lang), callback_data='ManualReg'),
            )
        )
    )


def get_menu_kbd(lang='ua'):
    return types.InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=(
            (
                types.InlineKeyboardButton(t('DUMMY', locale=lang), callback_data='DUMMY'),
            ),
        )
    )
