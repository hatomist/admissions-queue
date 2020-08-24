from aiogram import types
from i18n import t
import keyboards
import db
from main import AdmissionQueue
from stages import Stage
from utils import get_spherical_distance
import config
import logging
from aiogram.utils import exceptions
import prometheus

logger = logging.getLogger('commands')


def apply_handlers(aq: AdmissionQueue):
    async def start_handler(message: types.Message):
        prometheus.start_handler_cnt.inc({})
        user = await db.users.find_one({'uid': message.chat.id})
        if user is not None:
            if user['stage'] == Stage.menu:
                await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']),
                                     parse_mode=types.ParseMode.HTML)
            elif user['stage'] == Stage.geo:
                await db.users.find_one_and_update({'uid': user['uid']}, {'$set': {'stage': Stage.menu}})
                await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']),
                                     parse_mode=types.ParseMode.HTML)
            elif user['stage'] in [Stage.get_certnum, Stage.get_fio, Stage.template, Stage.register_btns]:
                await db.users.delete_one({'uid': user['uid']})
                await start_handler(message)  # recursive
                pass  # some other input expected
        else:
            await aq.aapi.register_user(message.from_user.id,
                                        message.from_user.mention[1:] if message.from_user.mention.startswith(
                                            '@') else None,
                                        message.from_user.first_name,
                                        message.from_user.last_name)

            if config.REGISTRATION:
                prometheus.user_registrations_cnt.inc({})
                user = db.users.insert_one({'uid': message.chat.id, 'lang': 'ua', 'stage': Stage.register_btns})
                await message.reply(t('PRE_REG', locale='ua'), reply_markup=keyboards.get_reg_kbd())
            else:
                user = db.users.insert_one({'uid': message.chat.id, 'lang': 'ua', 'stage': Stage.geo})
                await message.reply(t('MENU', locale='ua'), reply_markup=keyboards.get_menu_kbd(),
                                    parse_mode=types.ParseMode.HTML)

    async def help_handler(message: types.Message):
        prometheus.help_btn_cnt.inc({})
        await message.reply(t('SUPPORT'), reply_markup=keyboards.get_info_kbd())

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
            await query.message.answer(template['tokens'][0]['text'])

        elif query.data.startswith('AllQueues'):
            queues = (await aq.aapi.list_queues())['queues']
            num = len(list(filter(lambda x: x['active'], queues)))
            if num > 0:
                await query.message.edit_text(t('ALL_QUEUES', locale=user['lang']),
                                              reply_markup=keyboards.get_queues_kbd(queues, my_queues=False))
            else:
                await query.answer(t('NO_QUEUES', locale=user['lang']))

        elif query.data.startswith('MyQueues'):
            user_data = await aq.aapi.get_user_info(user['uid'])
            queues = user_data['queues']
            num = len(list(filter(lambda x: x['active'], queues)))
            if num > 0:
                await query.message.edit_text(t('MY_QUEUES', locale=user['lang']),
                                              reply_markup=keyboards.get_queues_kbd(queues, my_queues=True))
            else:
                await query.answer(t('NO_MY_QUEUES', locale=user['lang']))

        elif query.data.startswith('GetQueue'):
            user_data = await aq.aapi.get_user_info(user['uid'])
            queues = user_data['queues']
            queue_id = int(query.data.split('GetQueue', 1)[1])
            if any(map(lambda x: queue_id == x['id'], queues)):  # user already in queue
                query.data = f'GetMyQueue{queue_id}'  # edit data to pass query to GetMyQueue handler
                await query_handler(query)  # recursive call modified query
            else:
                await db.users.find_one_and_update({'uid': user['uid']},
                                                   {'$set': {'get_queue': queue_id, 'stage': Stage.geo}})
                return await query.message.answer(t('GEO', locale=user['lang']),
                                                  reply_markup=keyboards.get_geo_kbd(user['lang']))

        elif query.data.startswith('GetMyQueue'):
            prometheus.get_my_queue_cnt.inc({})
            user_data = await aq.aapi.get_user_info(user['uid'])
            queues = user_data['queues']
            queue_id = int(query.data.split('GetMyQueue', 1)[1])
            try:
                queue = list(filter(lambda x: queue_id == x['id'], queues))[0]
            except IndexError:
                return await query.answer(t('USER_NO_MORE_IN_QUEUE'), user['lang'])
            try:

                if queue['position']['status'] == 'processing':
                    await query.message.edit_text(t('USER_QUEUE_PROCESSING', locale=user['lang'],
                                                    queue_name=queue['name']),
                                                  reply_markup=keyboards.get_update_my_queue_kbd(queue_id,
                                                                                                 user['lang']),
                                                  parse_mode=types.ParseMode.HTML)

                elif queue['position']['status'] == 'waiting':
                    await query.message.edit_text(t('USER_QUEUE_INFO', locale=user['lang'],
                                                    queue_name=queue['name'],
                                                    pos=queue['position']['relativePosition']),
                                                  reply_markup=keyboards.get_update_my_queue_kbd(queue_id,
                                                                                                 user['lang']),
                                                  parse_mode=types.ParseMode.HTML)

                else:
                    logger.error('Unknown queue position status', queue['position']['status'])

                await query.answer()
            except exceptions.MessageNotModified:
                await query.answer(t('NO_UPDATES', locale=user['lang']))

        elif query.data.startswith('LeaveQueue'):
            queue_id = int(query.data.split('LeaveQueue', 1)[1])
            await db.users.find_one_and_update({'uid': user['uid']},
                                               {'$set': {'leave_queue': queue_id, 'stage': Stage.leave_queue}})
            return await query.message.edit_text(t('LEAVE_QUEUE'), reply_markup=keyboards.get_to_menu_kbd(user['lang']))

        elif query.data.startswith('RegInQueue'):
            prometheus.queue_registrations_cnt.inc({})
            queue_id = int(query.data.split('RegInQueue', 1)[1])
            await aq.aapi.add_user_to_queue(user['uid'], queue_id)
            await query.message.edit_text(t('REGISTER_IN_QUEUE_SUCCESS', locale=user['lang']),
                                          reply_markup=keyboards.get_menu_kbd(user['lang']))

        elif query.data.startswith('Menu'):
            await db.users.find_one_and_update({'uid': user}, {'$set': {'stage': Stage.menu}})
            await query.message.edit_text(t('MENU', locale=user['lang']),
                                          reply_markup=keyboards.get_menu_kbd(user['lang']),
                                          parse_mode=types.ParseMode.HTML)

        elif query.data.startswith('ChangeData'):
            await db.users.delete_one({'uid': user['uid']})
            await start_handler(query.message)
            await query.message.delete_reply_markup()

        else:
            logger.warning(f'Got invalid command {query.data}')

        await query.answer()

    async def location_handler(message: types.Message):
        lat = message.location.latitude
        lon = message.location.longitude
        user = await db.users.find_one({'uid': message.from_user.id})

        if user is None:
            return await start_handler(message)

        if user['stage'] != Stage.geo:
            return  # ignore

        if (get_spherical_distance(lat, lon, config.LAT, config.LON) > config.RADIUS) or \
                (message.forward_from is not None):
            return await message.reply(t('GEO_FAILED', locale=user['lang']), reply_markup=keyboards.get_geo_kbd())
        else:
            await db.users.find_one_and_update({'uid': message.from_user.id}, {'$set': {'stage': Stage.menu}})
            await message.reply(t('GEO_SUCCESS', locale=user['lang']),
                                reply_markup=types.ReplyKeyboardRemove())
            await aq.aapi.add_user_to_queue(user['get_queue'], user['uid'])

            user_data = await aq.aapi.get_user_info(user['uid'])
            queues = user_data['queues']
            queue_id = user['get_queue']
            queue = list(filter(lambda x: queue_id == x['id'], queues))[0]

            await message.answer(t('USER_QUEUE_INFO', locale=user['lang'], queue_name=queue['name'],
                                   pos=queue['position']['relativePosition']),
                                 reply_markup=keyboards.get_update_my_queue_kbd(queue_id,
                                                                                user['lang']),
                                 parse_mode=types.ParseMode.HTML)

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
            await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']),
                                 parse_mode=types.ParseMode.HTML)

        elif user['stage'] == Stage.template:
            data = {'t_' + user['template']['tokens'][user['template_stage']]['token']: message.text.strip()}

            if user['template_stage'] + 1 == user['tokens_num']:
                user['t_' + user['template']['tokens'][user['template_stage']]['token']] = message.text.strip()

                data = {}
                for key in user:
                    if key.startswith('t_'):
                        data[key.split('t_', 1)[1]] = user[key]

                await aq.aapi.set_user_details(user['uid'], data)

                await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']),
                                     parse_mode=types.ParseMode.HTML)

                return await db.users.find_one_and_update({'uid': user['uid']},
                                                          {'$set': {**data, 'stage': Stage.geo},
                                                           '$inc': {'template_stage': 1},
                                                           '$unset': {'template': ''}})

            await message.answer(user['template']['tokens'][user['template_stage'] + 1]['text'])

            await db.users.find_one_and_update({'uid': user['uid']},
                                               {'$set': {**data},
                                                '$inc': {'template_stage': 1}})

        elif user['stage'] == Stage.leave_queue:
            if message.text.strip().lower() in ['да', 'так', 'yes', 'д', 'y']:
                try:
                    await aq.aapi.remove_user_from_queue(user['leave_queue'], user['uid'])
                except KeyError:
                    pass  # ignore if already removed
                await db.users.find_one_and_update({'uid': user['uid']}, {'$set': {'stage': Stage.menu}})
                await message.answer(t('MENU', locale=user['lang']), reply_markup=keyboards.get_menu_kbd(user['lang']),
                                     parse_mode=types.ParseMode.HTML)

    handlers = [
        {'fun': start_handler, 'named': {'commands': ['start']}},
        {'fun': help_handler, 'named': {'commands': ['info', 'help', 'support']}},
        {'fun': location_handler, 'named': {'content_types': types.ContentType.LOCATION}},
        {'fun': text_handler, 'named': {'content_types': types.ContentType.TEXT}}
    ]

    for handler in handlers:
        aq.dp.register_message_handler(handler['fun'], **handler['named'])
    aq.dp.register_callback_query_handler(query_handler)
