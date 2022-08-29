import asyncio
import logging
import os
from os import getcwd, path
from aiohttp import web
import commands
from aiogram import Bot, Dispatcher, executor, types
import i18n

import config
from api import AdmissionAPI
from SafeBot import SafeBot
from urllib.parse import parse_qs
from aioprometheus import render, Registry, Counter, Service
import prometheus
from timer import Timer


class AdmissionQueue:
    def __init__(self):
        # Logging setup
        logging.basicConfig(level=config.LOGLEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

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

        # sendMessage endpoint setup

        async def send_message_handler(request: web.Request):
            if request.headers['Authorization'] != f'Bearer {aapi_token}':
                return web.Response(status=401)
            query = parse_qs(request.query_string)
            await self.bot.send_message(chat_id=query['uid'][0], text=query['text'][0],
                                        parse_mode=query['parse_mode'][0] if 'parse_mode' in query else None)
            return web.Response()

        async def broadcast_handler(request: web.Request):
            if request.headers['Authorization'] != f'Bearer {aapi_token}':
                return web.Response(status=401)
            query = await request.json()

            async def send():
                for uid in query['uids']:
                    await self.bot.send_message(chat_id=uid, text=query['text'],
                                                parse_mode=query['parse_mode'] if 'parse_mode' in query else None)
                    await asyncio.sleep(1/5)  # 5 msg/second
            t = Timer(0, send, False, True)
            return web.Response()

        webapp = web.Application()
        webapp.router.add_post('/sendMessage', send_message_handler)
        webapp.router.add_post('/broadcastMessage', broadcast_handler)

        # Prometheus setup
        self._prometheus_registry = Registry()
        self._prometheus_registry.register(prometheus.bot_requests_cnt)
        self._prometheus_registry.register(prometheus.user_registrations_cnt)
        self._prometheus_registry.register(prometheus.user_full_registrations_cnt)
        self._prometheus_registry.register(prometheus.queue_registrations_cnt)
        self._prometheus_registry.register(prometheus.get_my_queue_cnt)
        self._prometheus_registry.register(prometheus.geo_sent_cnt)
        self._prometheus_registry.register(prometheus.help_btn_cnt)
        self._prometheus_registry.register(prometheus.start_handler_cnt)
        self._prometheus_registry.register(prometheus.api_requests_cnt)

        prometheus.bot_requests_cnt.set({}, 0)
        prometheus.user_registrations_cnt.set({}, 0)
        prometheus.user_full_registrations_cnt.set({}, 0)
        prometheus.queue_registrations_cnt.set({}, 0)
        prometheus.get_my_queue_cnt.set({}, 0)
        prometheus.geo_sent_cnt.set({}, 0)
        prometheus.help_btn_cnt.set({}, 0)
        prometheus.start_handler_cnt.set({}, 0)
        prometheus.api_requests_cnt.set({}, 0)

        async def metrics_handler(request: web.Request):
            content, headers = render(self._prometheus_registry, [request.headers.get('accept')])
            return web.Response(body=content, headers=headers)

        webapp.router.add_get('/metrics', metrics_handler)

        # Run web server
        self.webapp = webapp
        self.site = None


if __name__ == '__main__':
    aq = AdmissionQueue()

    if 'WEBHOOK_HOST' in os.environ and os.environ['WEBHOOK_HOST']:
        host = os.environ['WEBHOOK_HOST']
        port = os.environ['WEBHOOK_PORT'] if 'WEBHOOK_PORT' in os.environ else 443

        async def on_startup(dp):
            await aq.bot.set_webhook(host)

        async def on_shutdown(dp):
            await aq.bot.delete_webhook()

        e = executor.set_webhook(aq.dp,
                                 webhook_path='/webhook',
                                 on_startup=on_startup,
                                 on_shutdown=on_shutdown,
                                 web_app=aq.webapp)

        e.run_app(host='0.0.0.0', port=port)

    else:
        async def on_startup(dp):
            runner = web.AppRunner(aq.webapp)
            await runner.setup()
            aq.site = web.TCPSite(runner, '0.0.0.0', 80)
            await aq.site.start()

        async def on_shutdown(dp):
            await aq.site.stop()
        executor.start_polling(aq.dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
