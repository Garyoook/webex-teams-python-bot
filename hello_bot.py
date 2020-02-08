import json
from poll import Poll
from flask import Flask, request

from translateObj import TranslateObj
from utils import create_webhook
from webexteamssdk import WebexTeamsAPI, Webhook
from googletrans import Translator, LANGUAGES

WEBEX_TEAMS_ACCESS_TOKEN = 'MDBjYmQxNmQtMWU5Zi00YTVkLTlmZjMtYjFiMDFhNTJhNmY1YWQ4N2M2NWYtODdh_PF84_4fd62afc-068e-4c49-b7bf-3ef92e2f33f5'

teams_api = None
all_polls = {}
translateObjs = {}
translator = Translator()

app = Flask(__name__)
@app.route('/messages_webhook', methods=['POST'])
def messages_webhook():
    if request.method == 'POST':
        webhook_obj = Webhook(request.json)
        return process_message(webhook_obj.data)

def process_message(data):
    if data.personId == teams_api.people.me().id:
        print (1)
        # Message sent by bot, do not respond
        return '200'
    else:
        message = teams_api.messages.get(data.id).text
        print(message)
        start = 1 if message[0] == '@' else 0
        commands_split = (message.split())[start:]
        command = ' '.join(commands_split)
        parse_message(command, data.personEmail, data.roomId)
        return '200'

def parse_message(command, sender, roomId):
    if command == "translation":
        if roomId not in list(translateObjs.keys()):
            create_trans(roomId,sender)
    if command == "start":
        if translateObjs[roomId]:
            start_translate(roomId, sender)
        if translateObjs[roomId]:
            end_translate(roomId, sender)
    if command == "voice":
        listen(roomId,sender)
    if command == "create poll":
        if roomId not in list(all_polls.keys()):
            create_poll(roomId, sender)
    elif command == "add option":
        if all_polls[roomId]:
            add_option(roomId, sender)
    elif command == "start poll":
        if all_polls[roomId]:
            start_poll(roomId, sender)
    elif command == "end poll":
        if all_polls[roomId]:
            end_poll(roomId, sender)
    return


def listen(roomId,sender):
    teams_api.messages.create(toPersonEmail=sender, text="发生啥事？")

def generate_translate_result_card(roomId, sourceText, targetText):
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Translate from: "
                },
                {
                    "type": "TextBlock",
                    "text": sourceText
                },
                {
                    "type": "TextBlock",
                    "text": "Result: "
                },
                {
                    "type": "TextBlock",
                    "text" : targetText
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                }
            ],
            "actions": []
        }
    }

def generate_start_translate_card(roomId): # like generate_start_poll_card
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please enter the message to be translated (English):"
                },
                {
                    "type": "Input.Text",
                    "id": "source_content",
                    "placeholder": "(English)",
                    "maxLength": 1024
                },
                {
                    "type": "TextBlock",
                    "text": "Please type target language below"
                },
                {
                    "type": "Input.Text",
                    "id": "target_lang",
                    "placeholder": "(e.g. zh-cn: chinese, ja: japanese, es: spanish, etc.)",
                    "maxLength": 500,
                    "isMultiline": True
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "OK"
                }
            ]
        }
    }

def generate_start_poll_card(roomId):
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please type your poll name below"
                },
                {
                    "type": "Input.Text",
                    "id": "poll_name",
                    "placeholder": "Poll Name",
                    "maxLength": 100
                },
                {
                    "type": "TextBlock",
                    "text": "Please type your poll description below"
                },
                {
                    "type": "Input.Text",
                    "id": "poll_description",
                    "placeholder": "Poll Description",
                    "maxLength": 500,
                    "isMultiline": True
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "OK"
                }
            ]
        }
    }

def generate_add_option_card(roomId):
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Please type the option you would like to add below:"
                },
                {
                    "type": "Input.Text",
                    "id": "option_text",
                    "placeholder": "Option Text",
                    "maxLength": 100
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "OK"
                }
            ]
        }
    }

def generate_voting_card(roomId):
    poll = all_polls[roomId]
    voting_options = {
        "type": "Input.ChoiceSet",
        "id": "poll_choice",
        "style": "expanded",
        "value": "1",
        "choices": []
    }
    for value, option in poll.options.items():
        voting_options["choices"].append({"title": option, "value": str(value)})
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "# Have your say on the poll below!"
                },
                {
                    "type": "TextBlock",
                    "text": "## " + all_polls[roomId].name
                },
                {
                    "type": "TextBlock",
                    "text": "### " + all_polls[roomId].description
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                },
                voting_options
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "OK"
                }
            ]
        }
    }

def generate_results_card(roomId, results):
    card_results = {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.1",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "# Below are the results!"
                },
                {
                    "type": "Input.Text",
                    "id": "roomId",
                    "value": roomId,
                    "isVisible": False
                }
            ],
            "actions": []
        }
    }
    for option, total in results.items():
        card_results["content"]["body"].append({
            "type": "TextBlock",
            "text": option + ": *" + str(total) + "*"
        })
    return card_results

def create_trans(roomId, sender):
    teams_api.messages.create(toPersonEmail=sender, text="Cards Unsupported", attachments=[generate_start_translate_card(roomId)])

def create_poll(roomId, sender):
    teams_api.messages.create(toPersonEmail=sender, text="Cards Unsupported", attachments=[generate_start_poll_card(roomId)])

def add_option(roomId, sender):
    teams_api.messages.create(toPersonEmail=sender, text="Cards Unsupported", attachments=[generate_add_option_card(roomId)])

def end_poll(roomId, sender):
    if all_polls[roomId].author == sender:
        if all_polls[roomId].started:
            teams_api.messages.create(roomId=roomId, text="Card Unsupported", attachments=[generate_results_card(roomId, all_polls[roomId].collate_results())])
        else:
            send_message_in_room(roomId, "Poll hasn't been started yet")
    else:
        send_message_in_room(roomId, "Only the poll's author can end the poll")

def start_translate(roomId, sender):
    if translateObjs[roomId].author == sender:
        if not translateObjs[roomId].started:
            translateObjs[roomId].started = True
            send_message_in_room(roomId, "Translating \"" + translateObjs[roomId].get_source_content() + "\" to " +
                                 LANGUAGES[translateObjs[roomId].get_target()])
        else:
            send_message_in_room(roomId, "Error: translation already started")
    else:
        send_message_in_room(roomId, "Error: only the translation author can start the translator")

def end_translate(roomId, sender):
    if translateObjs[roomId].author == sender:
        if translateObjs[roomId].started:
            source = translateObjs[roomId].get_source_content()
            target_lang = translateObjs[roomId].get_target()
            result = translator.translate(source, translateObjs[roomId].get_target(), 'en').text
            teams_api.messages.create(roomId=roomId, text="Card Unsupported", attachments=[generate_translate_result_card(roomId, source, result)])
        else:
            send_message_in_room(roomId, "Translation hasn't been started yet")
    else:
        send_message_in_room(roomId, "Only the translation's author can end the translation")

def start_poll(roomId, sender):
    if all_polls[roomId].author == sender:
        if not all_polls[roomId].started:
            all_polls[roomId].started = True
            teams_api.messages.create(roomId=roomId, text="Cards Unsupported", attachments=[generate_voting_card(roomId)])
        else:
            send_message_in_room(roomId, "Error: poll already started")
    else:
        send_message_in_room(roomId, "Error: only the poll author can start the poll")

@app.route('/attachmentActions_webhook', methods=['POST'])
def attachmentActions_webhook():
    if request.method == 'POST':
        print("attachmentActions POST!")
        webhook_obj = Webhook(request.json)
        return process_card_response(webhook_obj.data)

def process_card_response(data):
    attachment = (teams_api.attachment_actions.get(data.id)).json_data
    inputs = attachment['inputs']
    if 'poll_name' in list(inputs.keys()):
        add_poll(inputs['poll_name'], inputs['poll_description'], inputs['roomId'], teams_api.people.get(data.personId).emails[0])
        send_message_in_room(inputs['roomId'], "Poll created with title: " + inputs['poll_name'])
    elif 'option_text' in list(inputs.keys()):
        current_poll = all_polls[inputs['roomId']]
        current_poll.add_option(inputs['option_text'])
        send_message_in_room(inputs['roomId'], "Option added to poll \"" + current_poll.name + "\": " + inputs['option_text'])
        print(current_poll.name)
        print(current_poll.options)
    elif 'poll_choice' in list(inputs.keys()):
        current_poll = all_polls[inputs['roomId']]
        current_poll.votes[int(inputs["poll_choice"])] += 1
    elif 'source_content' in list(inputs.keys()):
        add_translateObj(inputs['source_content'], inputs['target_lang'], inputs['roomId'], teams_api.people.get(data.personId).emails[0])
        send_message_in_room(inputs['roomId'], "Translating: \"" + inputs['source_content'] +
                             "\" is ready to go,\n please type \"start\" to start the translation process, " +
                             "then \"show result\' to show the result")
        # Translated(src, dest, origin, text, pronunciation, extra_data=None)
    #     create translateObj here:
    return '200'

def add_poll(poll_name, poll_description, room_id, author):
    print(author)
    poll = Poll(poll_name, poll_description, room_id, author)
    all_polls[room_id] = poll

def add_translateObj(source_content, target_lang, roomId, author):
    print(author)
    translateObj = TranslateObj(source_content, target_lang, roomId, author)
    translateObjs[roomId] = translateObj

def send_direct_message(person_email, message):
    teams_api.messages.create(toPersonEmail=person_email, text=message)

def send_message_in_room(room_id, message):
    teams_api.messages.create(roomId=room_id, text=message)

if __name__ == '__main__':
    teams_api = WebexTeamsAPI(access_token=WEBEX_TEAMS_ACCESS_TOKEN)
    create_webhook(teams_api, 'messages_webhook', '/messages_webhook', 'messages')
    create_webhook(teams_api, 'attachmentActions_webhook', '/attachmentActions_webhook', 'attachmentActions')
    app.run(host='0.0.0.0', port=5000)
