from flask import Flask, request, send_file
from pymessenger import Bot
from docx import Document
import requests
from dotenv import load_dotenv
from os import environ
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = environ.get("PAGE_ACCESS_TOKEN")
bot = Bot(PAGE_ACCESS_TOKEN)

# Construct the database URI
POSTGRES_HOST = environ.get("POSTGRES_HOST")
POSTGRES_USER = environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD")
POSTGRES_DATABASE = environ.get("POSTGRES_DATABASE")

SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}'

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Rent(db.Model):
    __tablename__ = 'rent'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(100), nullable=False)
    name1 = db.Column(db.String(100), nullable=False)
    name2 = db.Column(db.String(100), nullable=False)
    current_state = db.Column(db.String(100), nullable=False)

class state(db.Model):
    __tablename__ = 'current_state'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(100), nullable=False)
    current_state = db.Column(db.String(100), nullable=False)

bot = Bot(PAGE_ACCESS_TOKEN)

conversation_state = {} 

def verify_token(req):
    if req.args.get("hub.verify_token") == VERIFY_TOKEN:
        print("Token was verified")
        return req.args.get("hub.challenge")
    else:
        print("Token was not verified ")
        return "incorrect"

@app.route("/webhook", methods=["GET", "POST"])
def listen():
    if request.method == "GET":
        return verify_token(request)
    if request.method == 'POST':
        payload = request.json
        print(payload)

        for entry in payload["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"): 
                    sender_id = messaging_event["sender"]["id"]        
                    message_text = messaging_event["message"]["text"]
                    response = process_message(message_text, sender_id,conversation_state)
                    if response:
                        bot.send_text_message(sender_id, response)

        return "ok"

def process_message(message_text, sender_id,conversation_state):
    text = message_text
    if sender_id not in conversation_state:
        conversation_state[sender_id] = {"step": 1, "answers": [], "contract_type": None}
        curstate = state(sender_id=sender_id,current_state = "1")
        db.session.add(curstate)
        db.session.commit()
    else:
        type = conversation_state[sender_id]["contract_type"]
        if type == "rental":
            return rental_contract(sender_id, text,conversation_state)
        elif type == "sale":
            return sale_contract(sender_id,text,conversation_state)
    if text == "สัญญาเช่า":
        return rental_contract(sender_id, text,conversation_state)
    elif text == "สัญญาขาย":
        return sale_contract(sender_id,text,conversation_state)
    else:
        return "ประเภทของสัญญาไม่ถูกต้อง"

def sale_contract(sender_id, text,conversation_state):
    pass
    
def rental_contract(sender_id, text, conversation_state):
    step = conversation_state[sender_id]["step"]
    curstate = state.query.filter_by(sender_id=sender_id).first()
    current_state_value = curstate.current_state
    print(current_state_value)
    if current_state_value == "1":
        conversation_state[sender_id]["contract_type"] = "rental"
        current_state_value = curstate.current_state = "2"
        db.session.commit()
        print(current_state_value)
        return ("กรุณากรอกชื่อผู้ทำสัญญาคนที่ 1")
    elif current_state_value == "2" and conversation_state[sender_id]["contract_type"] == "rental" and len(conversation_state[sender_id]["answers"]) == 0:
        conversation_state[sender_id]["answers"].append(text)
        conversation_state[sender_id]["step"] = 3
        return "กรุณากรอกชื่อผู้ทำสัญญาคนที่ 2"
    if step == 3 and len(conversation_state[sender_id]["answers"]) == 1:
        conversation_state[sender_id]["answers"].append(text)
        # Insert into database
        rent_entry = Rent(sender_id=sender_id, name1=conversation_state[sender_id]["answers"][0], name2=text,current_state = "1")
        db.session.add(rent_entry)
        db.session.commit()
        
        file_link = generate_document(sender_id, conversation_state[sender_id]["answers"])
        # Reset the conversation state for the next conversation
        del conversation_state[sender_id]
        return f"คลิกที่ลิงก์เพื่อดาวน์โหลดไฟล์: {file_link}"

        
def generate_document(sender_id, answers):
    doc = Document()
    doc.add_heading('สัญญาเช่าทั่วไป', 0)
    doc.add_paragraph(f'สัญญาฉบับนี้ทำขึ้นระหว่าง {answers[0]} และ {answers[1]}')
    file_path = 'contract.docx'
    doc.save(file_path)
    return upload_to_fileio(file_path)

def upload_to_fileio(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post('https://file.io/', files={'file': file})
        response_json = response.json()
        file_link = response_json.get('link')
    return file_link

@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)







