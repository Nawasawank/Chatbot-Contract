from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from os import environ
import threading
from database import db, State
from contracts.rental import rental_contract
import logging

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
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
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        abort(500, description="Internal Server Error")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        sender_id = event.source.user_id
        message_text = event.message.text
        app.logger.info(f"Handling message from user {sender_id}")
        app.logger.info(f"Message text: {message_text}")
        app.logger.info(f"Reply token: {event.reply_token}")

        thread = threading.Thread(target=process_and_reply, args=(event, sender_id, message_text))
        thread.start()
    except LineBotApiError as e:
        app.logger.error(f"An error occurred: {str(e)}")
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {str(e)}")

def process_and_reply(event, sender_id, message_text):
    with app.app_context():
        response = process_message(message_text, sender_id)
        if response:
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response)
                )
                app.logger.info("Reply sent successfully")
            except LineBotApiError as e:
                app.logger.error(f"An error occurred while replying: {str(e)}")

def process_message(message_text, sender_id):
    text = message_text
    curstate = State.query.filter_by(sender_id=sender_id).first()
    if not curstate:
        curstate = State(sender_id=sender_id, current_state="1", type_contract="")
        db.session.add(curstate)
        db.session.commit()
    else:
        if curstate.type_contract == "rental":
            return rental_contract(sender_id, text)
    if text == "สัญญาเช่า":
        return rental_contract(sender_id, text)
    else:
        return "ประเภทของสัญญาไม่ถูกต้อง"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

