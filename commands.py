from aiogram import types
from i18n import t
import keyboards
import db
from main import AdmissionQueue
from stages import Stage
from utils import get_spherical_distance
import config
import logging

logger = logging.getLogger('commands')


def apply_handlers(aq: AdmissionQueue):
    async def start_handler(message: types.Message):
        user = await db.users.find_one({'uid': message.from_user.id})
        if user is not None:
            if user['stage'] == Stage.menu:
                await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']))
            else:
                pass  # some other input expected
        else:
            await aq.aapi.register_user(message.from_user.id,
                                        message.from_user.mention if message.from_user.mention.startswith(
                                            '@') else None,
                                        message.from_user.first_name,
                                        message.from_user.last_name)

            if config.REGISTRATION:
                user = db.users.insert_one({'uid': message.from_user.id, 'lang': 'ua', 'stage': Stage.register_btns})
                await message.reply(t('PRE_REG', locale='ua'), reply_markup=keyboards.get_reg_kbd())
            else:
                user = db.users.insert_one({'uid': message.from_user.id, 'lang': 'ua', 'stage': Stage.geo})
                await message.reply(t('GEO', locale='ua'), reply_markup=keyboards.get_geo_kbd())

    async def query_handler(query: types.CallbackQuery):
        user = await db.users.find_one({'uid': query.from_user.id})
        if user is None:
            return await query.answer()

        if query.data.startswith('CertReg'):
            await db.users.find_one_and_update({'uid': user['uid']}, {'$set': {'stage': Stage.get_certnum}})
            return await query.message.edit_text(t('GET_CERTNUM'))

        elif query.data.startswith('ManualReg'):
            template = (await aq.aapi.get_registration_template())['template']
            num = len(template['tokens'])
            await db.users.find_one_and_update({'uid': user['uid']}, {'$set': {'stage': Stage.template,
                                                                               'template_stage': 0,
                                                                               'tokens_num': num,
                                                                               'template': template}})
            await query.message.answer(template['tokens'][0]['name'])

        else:
            logger.warning(f'Got invalid command {query.data}')

    async def location_handler(message: types.Message):
        lat = message.location.latitude
        lon = message.location.longitude
        user = await db.users.find_one({'uid': message.from_user.id})

        if user is None:
            return await message.reply(t('ERROR_RESTART'))

        if user['stage'] != Stage.geo:
            return  # ignore

        if get_spherical_distance(lat, lon, config.LAT, config.LON) > config.RADIUS:
            return await message.reply(t('GEO_FAILED', locale=user['lang']), reply_markup=keyboards.get_geo_kbd())
        else:
            await db.users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'stage': Stage.menu}})
            await message.reply(t('GEO_SUCCESS', locale=user['lang']),
                                reply_markup=types.ReplyKeyboardRemove())
            await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']))

    async def text_handler(message: types.Message):
        user = await db.users.find_one({'uid': message.from_user.id})

        if user is None:
            return await start_handler(message)

        elif user['stage'] == Stage.get_certnum:
            await db.users.find_one_and_update({'uid': user['uid']}, {'$set': {'certnum': message.text.strip(),
                                                                               'stage': Stage.get_fio}})
            return await message.reply(t('GET_FIO', locale=user['lang']))

        elif user['stage'] == Stage.get_fio:
            ret, retmsg = await aq.aapi.set_user_certificate(user['uid'], user['certnum'], message.text.strip())

            if ret == 400:
                return await message.reply(t('CERT_REG_FAILED', locale=user['lang'], reason=retmsg),
                                           reply_markup=keyboards.get_reg_kbd(user['lang']))

            await db.users.find_one_and_update({'uid': user['uid']},
                                               {'$set': {'stage': Stage.geo, 'fio': message.text}})
            await message.reply(t('GEO', locale=user['lang']), reply_markup=keyboards.get_geo_kbd(user['lang']))

        elif user['stage'] == Stage.template:
            data = {'t_' + user['template']['tokens'][user['template_stage']]['token']: message.text.strip()}

            if user['template_stage'] + 1 == user['tokens_num']:
                user['t_' + user['template']['tokens'][user['template_stage']]['token']] = message.text.strip()

                data = {}
                for key in user:
                    if key.startswith('t_'):
                        data[key.split('t_', 1)[1]] = user[key]

                await aq.aapi.set_user_details(user['uid'], data)

                await message.answer(t('GEO', locale=user['lang']), reply_markup=keyboards.get_geo_kbd(user['lang']))

                return await db.users.find_one_and_update({'uid': user['uid']},
                                                          {'$set': {**data, 'stage': Stage.geo},
                                                           '$inc': {'template_stage': 1},
                                                           '$unset': {'template': ''}})

            await message.answer(user['template']['tokens'][user['template_stage'] + 1]['name'])

            await db.users.find_one_and_update({'uid': user['uid']},
                                               {'$set': {**data},
                                                '$inc': {'template_stage': 1}})

    handlers = [
        {'fun': start_handler, 'named': {'commands': ['start']}},
        {'fun': location_handler, 'named': {'content_types': types.ContentType.LOCATION}},
        {'fun': text_handler, 'named': {'content_types': types.ContentType.TEXT}}
    ]

    for handler in handlers:
        aq.dp.register_message_handler(handler['fun'], **handler['named'])
    aq.dp.register_callback_query_handler(query_handler)
