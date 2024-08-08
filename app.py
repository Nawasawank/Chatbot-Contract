from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv
from os import environ
import threading
from database import db, State
from contracts.rental import rental_contract

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = environ.get("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

POSTGRES_HOST = environ.get("POSTGRES_HOST")
POSTGRES_USER = environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD")
POSTGRES_DATABASE = environ.get("POSTGRES_DATABASE")
SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/webhook", methods=['POST', 'GET'])
def webhook_handler():
    try:
        signature = request.headers.get('X-Line-Signature')
        if not signature:
            app.logger.error("X-Line-Signature header is missing.")
            abort(400, description="X-Line-Signature header is missing.")

        body = request.get_data(as_text=True)
        app.logger.info("Received LINE payload: " + body)
        handler.handle(body, signature)
        return 'OK'
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        abort(500, description="Internal Server Error")

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        thread = threading.Thread(target=process_and_reply, args=(event,))
        thread.start()
    except Exception as e:
        app.logger.error(f"An error occurred while replying: {str(e)}")

def process_and_reply(event):
    with app.app_context():
        sender_id = event.source.user_id
        message_text = event.message.text
        response = process_message(message_text, sender_id)

        if response:
            try:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=response)]
                        )
                    )
            except Exception as e:
                app.logger.error(f"An error occurred while sending the reply: {str(e)}")

def process_message(message_text, sender_id):
    curstate = State.query.filter_by(sender_id=sender_id).first()
    if not curstate:
        curstate = State(sender_id=sender_id, current_state="1", type_contract="")
        db.session.add(curstate)
        db.session.commit()
        return "Welcome! Please specify the type of contract you are interested in."

    if message_text == "สัญญาเช่า":
        curstate.type_contract = "rental"
        db.session.commit()
        return rental_contract(sender_id, message_text)

    if curstate.type_contract == "rental":
        return rental_contract(sender_id, message_text)
    else:
        return "ประเภทของสัญญาไม่ถูกต้อง"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
