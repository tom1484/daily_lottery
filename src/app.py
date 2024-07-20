import dotenv
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
    access_token=dotenv.get_key(".env", "CHANNEL_ACCESS_TOKEN")
)
handler = WebhookHandler(dotenv.get_key(".env", "CHANNEL_SECRET"))


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


# @handler.add(MessageEvent, message=TextMessageContent)
# def handle_message(event):
#     with ApiClient(configuration) as api_client:
#         line_bot_api = MessagingApi(api_client)
#         line_bot_api.reply_message_with_http_info(
#             ReplyMessageRequest(
#                 reply_token=event.reply_token,
#                 messages=[TextMessage(text=event.message.text)],
#             )
#         )


@scheduler.task("cron", id="push_statistics_update", day="*", hour="13")
# @scheduler.task("interval", id="push_statistics_update", seconds=10)
def push_statistics_update():
    count = lottery.update_history()
    if count == 0:
        return

    statistics = lottery.extract_statistics()
    messages = []

    # All records
    records = statistics["records"]
    message = "\n".join(records)

    messages.append(message)

    # Two-digit missing numbers
    missings = statistics["missings"]

    message = "前兩位缺號：\n"

    n = len(missings[0])
    for i, number in enumerate(missings[0]):
        message += f"{number:02d} "
        if i % 5 == 4 and i != n - 1:
            message += "\n"

    message += "\n\n"
    message += "後兩位缺號：\n"

    n = len(missings[1])
    for i, number in enumerate(missings[1]):
        message += f"{number:02d} "
        if i % 5 == 4 and i != n - 1:
            message += "\n"

    messages.append(message)

    with ApiClient(configuration) as api_client:
        for message in messages:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.broadcast(BroadcastRequest(messages=[TextMessage(text=message)]))


if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    app.run(port=5000)
