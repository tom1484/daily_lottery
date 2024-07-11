from flask import Flask, abort, request
from flask_apscheduler import APScheduler
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    BroadcastRequest,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import lottery

app = Flask(__name__)
scheduler = APScheduler()

configuration = Configuration(
    access_token="sRdmeIsFtWpRi89ardM+pPnT6QuonYhvjcE+4Mi3gAhBterF7PK9nXLOLb4SdrrDgljXeuhhWDmgCyuq3KZiRho/Oj4oOo/afuuSlSfBxSQEri/R1CdaoqLyQt0iIhezwjna+HVDoCCX+/B/9B1r2wdB04t89/1O/w1cDnyilFU="
)
handler = WebhookHandler("5ad835024e10773d53a1eb19eb1ef6ec")


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        # line_bot_api = MessagingApi(api_client)
        # line_bot_api.reply_message_with_http_info(
        #     ReplyMessageRequest(
        #         reply_token=event.reply_token,
        #         messages=[TextMessage(text=event.message.text)],
        #     )
        # )
        pass


@scheduler.task("cron", id="push_history_update", day="*", hour="12", minute="0")
# @scheduler.task("interval", id="push_history_update", seconds=10)
def push_history_update():
    count = lottery.update()
    if count == 0:
        return

    history = lottery.extract()
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.broadcast(BroadcastRequest(messages=[TextMessage(text=history)]))


if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    app.run(port=5000)
