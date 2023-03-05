from helpers.api_caller import APICaller
import helpers.utils as utils


class APICallerTelegram(APICaller):

    URL_TELEGRAM_SEND = '/bot{}/sendMessage'
    SECTION = "TELEGRAM-API"


    ########## Specific calls to Telegram API ##########
    def send_telegram_message (self, message:str):
        json_body = {
            "chat_id": utils.base64_decode(self._config.chat_id),
            "text": message,
            "parse_mode" : "markdown"
        }

        return self.do_post(self.URL_TELEGRAM_SEND.format(utils.base64_decode(self._config.bot_token)), json_body)