import asyncio
import base64
import logging
import shelve

from io import BytesIO

import yaml  # fades.pypi pyyaml == 3.12
import telepot  # fades.pypi == 12.1
import telepot.aio
from telepot.aio.loop import MessageLoop

from aiosmtpd.controller import Controller  # fades.pypi == 1.1
from aiosmtpd.handlers import Message


class UnifiAlertMessage(Message):

    def __init__(self, bot):
        super(UnifiAlertMessage, self).__init__()
        self.bot = bot

    def handle_message(self, message):
        logging.info("Received email, bot state: %s - subject: %s",
                     self.bot.active, message.get('subject', 'no-subject'))
        if not self.bot.active:
            logging.info("Bot is not active, ignoring email")
            return

        parts = [part for part in message.walk()
                 if part.get_content_type() == 'image/jpeg']
        if not parts:
            self.bot.sendMessage(message['subject'])
        for part in parts:
            image = BytesIO(base64.decodebytes(
                part.get_payload().encode('utf-8')))
            self.bot.sendPhoto(image, message['subject'])

    async def smtpd_main(self, hostname, port):
        controller = Controller(self, hostname=hostname, port=port)
        controller.start()


class AlertBot:
    message_limit = 1
    no_call = 0

    def __init__(self, bot, loop, valid_users, state):
        super(AlertBot, self).__init__()
        self.valid_users = valid_users
        self.state = state
        self.loop = loop
        self.bot = bot
        self.active = self.state.get('active')

    def sendMessage(self, message):
        if self.state.get('group') and self.active:
            self.loop.create_task(self.bot.sendMessage(
                self.state.get('group')['id'], message))

    def sendPhoto(self, image, caption):
        self.loop.create_task(self.bot.sendPhoto(
            chat_id=self.state.get('group')['id'], photo=image, caption=caption))

    async def handle(self, message):
        content_type, chat_type, chat_id = telepot.glance(message)
        logging.info("Message received: content: %s, type: %s, chat_id: %s, "
                     "msg: %s", content_type, chat_type, chat_id, message)
        user = message['from']['id']  # was username, some users don't have one
        if user not in self.valid_users:
            logging.warning("Message from UNKNOWN user: %s, content: %s, type:"
                            " %s, chat_id: %s, msg: %s", user, content_type,
                            chat_type, chat_id, message)
            return
        if 'text' not in message:
            logging.debug("Ignoring message: %s", message)
            return
        if chat_type == 'group' and message['text'] == '/start':
            group = self.state.get('group')
            if group:
                logging.warning("Already bound to a group: %s", group['title'])
                if group['id'] == chat_id:
                    await self.bot.sendMessage(chat_id, "Already using this group")
            else:
                self.state['group'] = message['chat']
                return
        if message['text'] in ['/e', '/enable']:
            self.active = True
            self.state['active'] = self.active
        elif message['text'] in ['/d', '/disable']:
            self.active = False
            self.state['active'] = self.active
        elif message['text'] in ['/status']:
            status = "The bot is active and sharing motion events" \
                if self.active else "The bot is currently not sharing motion events"
            await self.bot.sendMessage(chat_id, status)


def main(config, state):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    loop = asyncio.get_event_loop()
    bot = telepot.aio.Bot(config['token'])
    alert_bot = AlertBot(bot, loop, config['valid_users'], state)
    email_handler = UnifiAlertMessage(alert_bot)
    smtp_listen = config.get('smtp_listen', '0.0.0.0')
    smtp_port = config.get('smtp_port', 8025)

    loop.create_task(email_handler.smtpd_main(smtp_listen, smtp_port))
    loop.create_task(MessageLoop(bot, alert_bot.handle).run_forever())

    logging.info("Bot and SMTP server starting...")
    loop.run_forever()


if __name__ == '__main__':
    # load config
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    options = parser.parse_args()
    with open(options.config, 'r') as fd:
        config = yaml.safe_load(fd)
    state = shelve.open(config['state_file'])
    main(config, state)
