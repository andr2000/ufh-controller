import config
from collections import deque
import http.client
import logging
import urllib.parse

logger = logging.getLogger(__name__)
telegram_url = 'api.telegram.org'
bot_token = config.options['telegram_bot_token']
chat_id = config.options['telegram_chat_id']
msg_queue = deque()

# To get chat_id:
# 1. https://api.telegram.org/bot<yourtoken>/getUpdates
# 2. Say something in the mobile app to the bot
# 3. Refresh the page 1) and get the chat_id


def send_message_now(msg):
    if not bot_token or not chat_id:
        return

    try:
        conn = http.client.HTTPSConnection(telegram_url, 443, timeout=5)
        conn.request('GET', ' /' + 'bot' + bot_token +
                     '/sendMessage?chat_id=' + chat_id + '&text=' +
                     urllib.parse.quote_plus(msg))
        # Do not check the response - we don't care if we fail
    except Exception:
        pass


def send_message(msg):
    global msg_queue

    if not bot_token or not chat_id:
        return

    msg_queue.appendleft(msg)


def process():
    if not bot_token or not chat_id:
        return

    if not len(msg_queue):
        return

    try:
        conn = http.client.HTTPSConnection(telegram_url, 443, timeout=5)
        msg = ''
        while len(msg_queue):
            msg += msg_queue.pop() + '\n'
        conn.request('GET', ' /' + 'bot' + bot_token +
                     '/sendMessage?chat_id=' + chat_id + '&text=' +
                     urllib.parse.quote_plus(msg))
        # Do not check the response - we don't care if we fail
    except Exception:
        pass
