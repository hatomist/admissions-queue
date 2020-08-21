import logging
import os
from os import getcwd, path
import commands
from aiogram import Bot, Dispatcher, executor, types
import i18n


class AdmissionQueue:
    def __init__(self):
        # Logging setup
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'   )

        # Bot setup
        try:
            self.bot = Bot(token=os.environ['BOT_TOKEN'])
        except KeyError:
            logging.critical('Please specify BOT_TOKEN ENV variable')
            exit(-1)
        self.dp = Dispatcher(self.bot)
        commands.apply_handlers(self.dp)

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


if __name__ == '__main__':
    aq = AdmissionQueue()
    executor.start_polling(aq.dp, skip_updates=True)
