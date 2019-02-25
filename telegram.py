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
msg_current = ''

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
    except Exception:
        # If we fail then add to the queue - this might be a short(?)
        # temporary brownout
        msg_queue.appendleft(msg + '\n')


def send_message(msg):
    global msg_queue

    if not bot_token or not chat_id:
        return

    msg_queue.appendleft(msg + '\n')


def process():
    global msg_current

    if not bot_token or not chat_id:
        return

    len_msg_current = len(msg_current)
    if not len(msg_queue) and not len_msg_current:
        return

    # FIXME: Telegram supports messages up to 4KiB, so drop the oldest first
    while len(msg_queue) + len_msg_current > 4 * 1024:
        msg_queue.pop()

    try:
        conn = http.client.HTTPSConnection(telegram_url, 443, timeout=5)
        # Take what we have for retry...
        msg = msg_current
        # ...and append any new messages
        while len(msg_queue):
            msg += msg_queue.pop()
        conn.request('GET', ' /' + 'bot' + bot_token +
                     '/sendMessage?chat_id=' + chat_id + '&text=' +
                     urllib.parse.quote_plus(msg))
        msg_current = ''
    except Exception:
        # Save for retry
        msg_current += msg
