from flask import Flask, request, jsonify, render_template
import os
import dialogflow
import dialogflow_v2
import requests
import json
import pusher

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/bot', methods=['GET', 'POST'])
def bot():
    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':
        data = request.get_json(silent=True)
        recharge = data['queryResult']['parameters']['Recharge']

        reply = {
            "fulfillmentText": recharge,
        }
        return jsonify(reply)


@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    fulfillment_text = detect_intent_texts(project_id, "unique", message, 'en')
    response_text = {'message':  fulfillment_text}

    return jsonify(response_text)


def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    if text:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(
            session=session, query_input=query_input)

        return response.query_result.fulfillment_text


@app.route('/intents', methods=['POST', 'GET'])
def intents():
    if request.method == 'GET':
        return render_template('intents.html')
    if request.method == 'POST':
        intent_name = request.form['intent_name']
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        training_phrases_parts = ''
        message_texts = ''
        create_intent(project_id, intent_name, training_phrases_parts, message_texts)

        return render_template('intents.html')


def create_intent(project_id, display_name, training_phrases_parts,
                  message_texts):
    """Create an intent of the given intent type."""
    intents_client = dialogflow_v2.IntentsClient()

    parent = intents_client.project_agent_path(project_id)
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = dialogflow_v2.types.Intent.TrainingPhrase.Part(
            text=training_phrases_part)
        # Here we create a new training phrase for each provided part.
        training_phrase = dialogflow_v2.types.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow_v2.types.Intent.Message.Text(text=message_texts)
    message = dialogflow_v2.types.Intent.Message(text=text)

    intent = dialogflow_v2.types.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message])

    response = intents_client.create_intent(parent, intent)

    print('Intent created: {}'.format(response))


# run Flask app
if __name__ == "__main__":
    app.run(debug=True)
