from flask import Flask, request, jsonify, render_template,make_response, redirect, url_for, flash, sessions, session, get_flashed_messages
import os
import dialogflow
import requests
import json
import pusher
import time
import variable
from dataset import getDataFromPhone, getRecords, checkOrderId
# from speech import  SpeechToText

app = Flask(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="GOOGLE_APPLICATION_CREDENTIALS.json"
os.environ["DIALOGFLOW_PROJECT_ID"]="DIALOGFLOW_PROJECT_ID"
os.environ["OMDB_API_KEY"]="OMDB_API_KEY"

# initialize Pusher
pusher_client = pusher.Pusher(
  app_id='PUSHER_APP_ID',
  key='KEY',
  secret="PUSHER_SECRET_KEY",
  cluster='ap2',
  ssl=True
)

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/switch', methods=['POST'])
def switch():
    cust_name = variable.cust_name
    cust_phone = variable.cust_phone
    cust_user_id = variable.cut_uid
    cust_records = variable.records
    cust_order_id = variable.order_id
    return render_template('switch.html', cust_phone=cust_phone, cust_name=cust_name, cust_user_id=cust_user_id, cust_records=cust_records, cust_order_id=cust_order_id)

# @app.route('/voice')
# def voice():
#     session['message'] = str(SpeechToText())
#     # return SpeechToText()

@app.route('/main', methods=['GET', 'POST'])
def main():
    variable.hello_ctr = 0
    variable.cust_name = -1
    variable.cust_phone = ""
    variable.cut_uid = -1
    variable.records = {}
    phone_no = str(request.form.get('phone_no'))
    name, uid = getDataFromPhone(phone_no)
    if uid!=-1:
        records = getRecords(uid)
        variable.cust_name = name
        variable.cust_phone = phone_no
        variable.cut_uid = uid
        variable.records = records
    return render_template('main.html')


@app.route('/get_movie_detail', methods=['POST'])
def get_movie_detail():
    data = request.get_json(silent=True)

    try:
        movie = data['queryResult']['parameters']['movie']
        api_key = os.getenv('OMDB_API_KEY')

        movie_detail = requests.get('http://www.omdbapi.com/?t={0}&apikey={1}'.format(movie, api_key)).content
        movie_detail = json.loads(movie_detail)

        response = """
            Title : {0}
            Released: {1}
            Actors: {2}
            Plot: {3}
        """.format(movie_detail['Title'], movie_detail['Released'], movie_detail['Actors'], movie_detail['Plot'])
    except:
        response = "Could not get movie detail at the moment, please try again"

    reply = {"fulfillmentText": response}

    return jsonify(reply)

def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    
    if text:
        text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        return response


@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        socketId = request.form['socketId']
    except KeyError:
        socketId = ''

    name = variable.cust_name
    uid = variable.cut_uid
    phone_no = variable.cust_phone


    # print(name, phone_no, uid, records[0])

    if uid!=-1:
        records = variable.records
        f_text = 'Hi ' + name + ', Welcome to our Customer Support Portal, all our Customer Care Executives are busy right now. So let me assist you. Your most recent purchase with us was ' + records[0][2] + ". If your query is regarding this order, please say yes otherwise no."
    else:
        f_text = "Hi, Welcome to our Customer Support Portal, all our Customer Care Executives are busy right now. So let me assist you. Please let me know your registered mobile number."



    message = request.form['message']
    # message = session.message
    # print('MESSAGE: ',message)
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    response = detect_intent_texts(project_id, 7014106276, message, 'en')
    fulfillment_text = response.query_result.fulfillment_text

    if response.query_result.action == 'input.welcome':
        if variable.hello_ctr == 0:
            fulfillment_text = f_text
            if uid!=-1:
                variable.hello_ctr += 1
            response_text = {"message": fulfillment_text}
            pusher_client.trigger(
                'movie_bot',
                'new_message',
                {
                    'human_message': message,
                    'bot_message': fulfillment_text,
                },
                socketId
            )

            return jsonify(response_text)

    if uid==-1:
        if response.query_result.action=='input.registered_mobile':
            message = request.form['message']
            phone_no = str(str(response.query_result.parameters.fields['phone_no'].list_value.values)[16:-3])
            name, uid = getDataFromPhone(phone_no)
            if uid != -1:
                records = getRecords(uid)
                variable.records = records
                variable.cust_name = name
                variable.cust_phone = phone_no
                variable.cut_uid = uid
                fulfillment_text = 'Hi ' + name + ', Welcome to our Customer Support Portal, all our Customer Care Executives are busy right now. So let me assist you. Your most recent purchase with us was ' + \
                         records[0][2] + ". If your query is regarding this order, please say yes otherwise no."
            else:
                fulfillment_text = 'Could not find this number in our records. Please tell us a registered mobile number.'

            response_text = {"message": fulfillment_text}
            pusher_client.trigger(
                'movie_bot',
                'new_message',
                {
                    'human_message': message,
                    'bot_message': fulfillment_text,
                },
                socketId
            )

            return jsonify(response_text)



    records = variable.records
    order_id = records[0][0]
    variable.order_id=order_id
    order_status = records[0][-2]
    if response.query_result.action=='input.order_id':
        order_id = int(str(response.query_result.parameters.fields['order_number'].list_value.values)[15:-4])

        if checkOrderId(order_id, uid)!=-1:
            recent_record = checkOrderId(order_id, uid)
            order_id = str(recent_record[0])
            variable.order_id=order_id
            order_status = recent_record[-2]
            if order_status == 'Delievered':
                fulfillment_text = 'Do you want to know the status of the order or file a complaint?'
            else:
                fulfillment_text = 'Do you want to know the status of the order or cancel the order?'
        else:
            fulfillment_text = 'You provided invalid order id. Please tell us a correct order id.'
        response_text = {"message": fulfillment_text}
        pusher_client.trigger(
            'movie_bot',
            'new_message',
            {
                'human_message': message,
                'bot_message': fulfillment_text,
            },
            socketId
        )
        return jsonify(response_text)

    if response.query_result.action == 'input.recent_yes':
        recent_record = records[0]
        order_id = recent_record[0]
        variable.order_id=order_id
        order_status = recent_record[-2]
        if order_status == 'Delievered':
            fulfillment_text = 'Do you want to know the status of the order or file a complaint?'
        else:
            fulfillment_text = 'Do you want to know the status of the order or cancel the order?'

    if response.query_result.action=='input.recent_no':
        recent_record = checkOrderId(order_id, uid)
        order_id = recent_record[0]
        variable.order_id=order_id
        order_status = recent_record[-2]



    if response.query_result.action == 'input.status':
        fulfillment_text = 'Your order tracked with status - ' + order_status + '.'

    if response.query_result.action == 'input.cancel':
        fulfillment_text = 'Your order is cancelled'

    if response.query_result.action == 'input.complaint':
        fulfillment_text = 'Please tell us your complaint with the product.'

    if response.query_result.action == 'input.complaint_details':
        fulfillment_text = 'Your complaint is successfully registered.'





    response_text = {"message": fulfillment_text}
    pusher_client.trigger(
        'movie_bot',
        'new_message',
        {
            'human_message': message,
            'bot_message': fulfillment_text,
        },
        socketId
    )

    return jsonify(response_text)



# run Flask app
if __name__ == "__main__":
    app.secret_key = 'secret12'
    app.run('localhost', 1231, debug=True)
