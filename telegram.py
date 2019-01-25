import config
import http.client
import logging
import urllib.parse

logger = logging.getLogger(__name__)
telegram_url = 'api.telegram.org'
bot_token = config.options['telegram_bot_token']
chat_id = config.options['telegram_chat_id']

# To get chat_id:
# 1. https://api.telegram.org/bot<yourtoken>/getUpdates
# 2. Say something in the mobile app to the bot
# 3. Refresh the page 1) and get the chat_id


def send_message(msg):
    if not bot_token or not chat_id:
        return

    try:
        conn = http.client.HTTPSConnection(telegram_url, 443)
        conn.request('GET', ' /' + 'bot' + bot_token +
                     '/sendMessage?chat_id=' + chat_id + '&text=' +
                     urllib.parse.quote_plus(msg))
        # Do not check the response - we don't care if we fail
    except Exception:
        pass
