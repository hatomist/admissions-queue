import logging
import os
from os import getcwd, path
from aiohttp import web
import commands
from aiogram import Bot, Dispatcher, executor, types
import i18n
from api import AdmissionAPI
from SafeBot import SafeBot
from urllib.parse import parse_qs


class AdmissionQueue:
    def __init__(self):
        # Logging setup
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Bot setup
        try:
            self.bot = SafeBot(token=os.environ['BOT_TOKEN'])
            Bot.set_current(self.bot)  # just to be sure with all of that class override things
        except KeyError:
            logging.critical('Please specify BOT_TOKEN ENV variable')
            exit(-1)
        self.dp = Dispatcher(self.bot)
        commands.apply_handlers(self)

        try:
            aapi_host = os.environ['AAPI_HOST']
        except KeyError:
            logging.critical('Please specify AAPI_HOST (admission api host link) ENV variable')
            exit(-1)

        try:
            aapi_token = os.environ['AAPI_TOKEN']
        except KeyError:
            logging.critical('Please specify AAPI_TOKEN (admission api bearer token) ENV variable')
            exit(-1)

        # noinspection PyUnboundLocalVariable
        self.aapi = AdmissionAPI(aapi_host, aapi_token)
        # i18n setup

        cwd = getcwd()
        translations_dir = path.abspath(path.join(cwd, 'translations'))
        if not path.isdir(translations_dir):
            logging.error(f"i18n: Translations path ({translations_dir}) does not exist")
            exit(-1)

        i18n.load_path.append(translations_dir)
        i18n.set('filename_format', '{locale}.{format}')
        i18n.set('locale', 'ua')
        i18n.set('fallback', 'ua')

        async def send_message_handler(request: web.Request):
            if request.headers['Authorization'] != f'Bearer {aapi_token}':
                return web.Response(status=401)
            query = parse_qs(request.query_string)
            await self.bot.send_message(chat_id=query['uid'][0], text=query['text'][0],
                                        parse_mode=query['parse_mode'][0] if 'parse_mode' in query else None)
            return web.Response()

        webapp = web.Application()
        webapp.router.add_post('/sendMessage', send_message_handler)

        web.run_app(webapp, port=5006, host='127.0.0.1')


if __name__ == '__main__':
    aq = AdmissionQueue()

    if 'WEBHOOK_HOST' in os.environ:
        host = os.environ['WEBHOOK_HOST']
        port = os.environ['WEBHOOK_PORT']


        async def on_startup(dp):
            await aq.bot.set_webhook(host)

        async def on_shutdown(dp):
            await aq.bot.delete_webhook()

        executor.start_webhook(
            aq.dp,
            webhook_path='',
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            host='localhost',
            port=port
        )

    else:
        executor.start_polling(aq.dp, skip_updates=True)
