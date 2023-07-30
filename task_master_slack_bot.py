# from bottle import Bottle, request, run
from enum import Enum
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import re
import json
import random
import requests
import hashlib
import hmac
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# loads from .env file
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
signing_secret = os.environ['SIGNING_SECRET']

class RequestType(Enum):
    PERFORM_TASK = "Task Request :wrench:"
    REVIEW_PULL_REQUEST = "Pull Request Review :computer:"
    INSPECT_THREAD_OR_LINK = "Inspection Request :eyes:"

async def is_valid_signature(request: Request):
    timestamp = request.headers.get('X-Slack-Request-Timestamp')
    request_body = await request.body()
    slack_signature = request.headers.get('X-Slack-Signature')
    basestring = f'v0:{timestamp}:{request_body.decode("utf-8")}'.encode('utf-8')

    computed_signature = 'v0=' + hmac.new(
        bytes(signing_secret, 'utf-8'),
        basestring,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, slack_signature)


# slack API for handling slack command - https://api.slack.com/interactivity/slash-commands
@app.post('/do')
async def perform_task(request: Request):
    response = await review(request, RequestType.PERFORM_TASK )
    return response
@app.post('/git-review')
async def review_git(request: Request):
    response = await review(request, RequestType.REVIEW_PULL_REQUEST )
    return response
@app.post('/inspect')
async def inspect(request : Request):
    response = await review(request, RequestType.INSPECT_THREAD_OR_LINK )
    return response

async def review(request, request_type):
    if not await is_valid_signature(request):
        response_data = {'response_type': 'ephermal', 'text': ':no_entry_sign: Error (403_invalid_request) - An error has occurred. Please contact Admin.'}
        return response_data
    form_data = await request.form()
    response_url = form_data.get('response_url')
    initiator = form_data.get('user_id')
    channel_id = form_data.get('channel_id')
    command = form_data.get('command')
    slack_message = form_data.get('text').split()
    if len(slack_message) == 1 or len(slack_message) > 2:
        is_assignee_random = True
    elif len(slack_message) == 2:
        is_assignee_random = False
    else:
        response_data = { 'response_type' : 'ephemeral', 'text' : ':no_entry_sign: Error - Invalid Slack Command. Please check /help to see details.' }
        return response_data

    # print(f"command : {command}, slack_message : {slack_message}, initiator {initiator}, channel_id {channel_id}, link {link}, response url {response_url}")
    if request_type == RequestType.PERFORM_TASK:
        task = slack_message[0]
        asyncio.ensure_future(post_to_slack(slack_message= slack_message, task=task, link=None, channel_id= channel_id, initiator= initiator, response_url=response_url, request_type=request_type, is_assignee_random = is_assignee_random))  # Run the async function in the background
        response_data = { 'response_type' : 'ephemeral', 'text' : f'Your command ({command}) has been received. Please wait for the results :hourglass:' }
        return response_data
    else:
        # request_type==RequestType.REVIEW_PULL_REQUEST OR request_type==RequestType.INSPECT_THREAD_OR_LINK
        link = slack_message[0]
        if is_valid_url(link, request_type):
            asyncio.ensure_future(post_to_slack(slack_message= slack_message, task=None, link=link, channel_id= channel_id, initiator= initiator, response_url=response_url, request_type=request_type, is_assignee_random = is_assignee_random))  # Run the async function in the background
            response_data = { 'response_type' : 'ephemeral', 'text' : f'Your command ({command}) has been received. Please wait for the results :hourglass:' }
            return response_data
        else:
            response_data = { 'response_type' : 'ephemeral', 'text' : ':no_entry_sign: Error - Invalid Github PR link. Please put valid Url.' }
            return response_data


async def post_to_slack(slack_message, task, link, channel_id, initiator, response_url, request_type, is_assignee_random):
    if is_assignee_random:
        if len(slack_message) > 2:
            # multiple assignees, need to randomize
            assignee = random.choice(slack_message[1:])
            response_data = success_response(
                type=request_type,
                initiator=initiator,
                assignee=assignee,
                link=link,
                task=task,
                is_assignee_random=True)
            requests.post(response_url, json.dumps(response_data))
        else:
            # need to randomize out of all group members   
            conv_members_response = client.conversations_members(channel=channel_id)
            if not conv_members_response["ok"]:
                response_data = {'response_type': 'ephermal', 'text': ':no_entry_sign: Error (err_conversations_members) - An error has occurred. Please contact Admin.'}
                return json.dumps(response_data)
            members = conv_members_response["members"]
            # Select a random member from the list
            random_member_id = random.choice(members)
            assignee = is_bot_or_command_user(random_member_id)
            while initiator == random_member_id or assignee[1]:
                random_member_id = random.choice(members)
                assignee = is_bot_or_command_user(random_member_id)

            response_data = success_response(
                type= request_type,
                initiator=initiator,
                assignee=f"<@{assignee[0]['id']}>",
                link=link,
                task=task,
                is_assignee_random=True)
            requests.post(response_url, json.dumps(response_data))
    else:
        # only one assignee
        assignee = slack_message [1]
        response_data = success_response(
            type=request_type,
            initiator=initiator,
            assignee=assignee,
            link=link,
            task=task,
            is_assignee_random=False)
        requests.post(response_url, json.dumps(response_data))




def is_valid_url(url, request_type):
    escaped_url = extract_url(url)
    if request_type == RequestType.REVIEW_PULL_REQUEST:
        pattern = r'^https:\/\/github\.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+\/pull\/[0-9]+$'
        match = re.match(pattern, escaped_url)
        return bool(match)
    else:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        match = re.match(pattern, escaped_url)
        return bool(match)

def extract_url(text):
    pattern = r'<(.*?)>'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None


def is_bot_or_command_user(user_id):
    response = client.users_info(user=user_id)
    if response['ok']:
        user = response['user']
        if user['is_bot'] or user['is_app_user']:
            return (user, True)
        else:
            return (user, False)
    return (None, False)

def success_response (type, initiator, assignee, task, link, is_assignee_random):

    if type == RequestType.PERFORM_TASK:
        response_data = {
        "response_type" : "in_channel",
        "text" : f":computer: {assignee} was requested to take a look at {link} :eyes:.\n Request initiated by {initiator} :saluting_face:",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*You have a new request :gift:*\n {assignee}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type*\n {type.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Task :rocket:*\n {task}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Requested By:*\n <@{initiator}>"
                    }
                ]
            }
        ]
        }
    else:
        response_data = {
        "response_type" : "in_channel",
        "text" : f":computer: {assignee} was requested to take a look at {link} :eyes:.\n Request initiated by {initiator} :saluting_face:",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*You have a new request :gift:*\n {assignee}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type*\n {type.value}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Link / Thread :rocket:*\n {link}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Requested By:*\n <@{initiator}>"
                    }
                ]
            }
        ]
        }


    if is_assignee_random:
        response_data['blocks'].append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":game_die: The user was randomly chosen by :robot_face:"
                }
            ]
        })
        response_data['text'] = f":computer: {assignee} was picked randomly by me :robot_face: to take a look at {link} :eyes:.\n Request initiated by {initiator} :saluting_face:"
    
    return response_data

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='localhost', port=5000)