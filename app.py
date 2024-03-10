from flask import Flask, request, send_file
from pymessenger import Bot
from docx import Document
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "VF token for education ecosystem"
PAGE_ACCESS_TOKEN = 'EAAKZC9fRhwiYBOZCHby87Mxhx5Q7OcIFRfE7pLFSZC4XfHKGebbiRTYNxU6pCEdl4DtZByXuPUdaAGEAZA45GJlDgt57ZBTFN6ZBDz8OWcBncQ4V73KXIjws0BOf31nqUiBOPtbupZBziykCChLgdHzBai7ySIsJIJZBw5zACnIXn4tXzwptlNbFVawsA5m27C8nx'
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
                    response = process_message(message_text, sender_id)
                    if response:
                        bot.send_text_message(sender_id, response)

        return "ok"

def process_message(message_text, sender_id):
    text = message_text
    if sender_id not in conversation_state:
        conversation_state[sender_id] = {"step": 1, "answers": [], "contract_type": None}

    step = conversation_state[sender_id]["step"]
    if step == 1:
        if text == "สัญญาเช่า":
            conversation_state[sender_id]["contract_type"] = "rental"
            rental_contract(sender_id, text)
            conversation_state[sender_id]["step"] = 2
            return "กรุณากรอกชื่อผู้ทำสัญญาคนที่ 1"
        else:
            return "ประเภทของสัญญาไม่ถูกต้อง"
    elif step == 2 or step == 3:
        if conversation_state[sender_id]["contract_type"] == "rental":
            return rental_contract(sender_id, text)
        elif conversation_state[sender_id]["contract_type"] == "sales":
            return
    
def rental_contract(sender_id, text):
    step = conversation_state[sender_id]["step"]
    if step == 2:
        if len(conversation_state[sender_id]["answers"]) == 0:
            conversation_state[sender_id]["answers"].append(text)
            conversation_state[sender_id]["step"] = 3
            return "กรุณากรอกชื่อผู้ทำสัญญาคนที่ 2"
    elif step == 3:
        if len(conversation_state[sender_id]["answers"]) == 1:
            conversation_state[sender_id]["answers"].append(text)
            file_link = generate_document(sender_id, conversation_state[sender_id]["answers"])
            # Reset the conversation state for the next conversation
            del conversation_state[sender_id]
            return f"สำเร็จแล้ว! คลิกที่ลิงก์เพื่อดาวน์โหลดไฟล์: {file_link}"

        
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






