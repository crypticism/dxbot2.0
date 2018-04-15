import os
import time
import re

import psycopg2

from slackclient import SlackClient
from lib.quotes import addQuote, getQuote

# Create client
client = SlackClient(os.environ.get('DXBOT_TOKEN'))
# User ID: Set after connecting
dxbot_id = None
users = []
user_map = {}
last_event = None

# Constants
READ_DELAY = 1  # 1 second read delay
COMMAND_REGEX = r"^!(?P<command>\w+) ?(?P<message>.*)?$"
EXCLUSION_LIST = [
    'slackbot',
    'scryfall',
    'dx_bot',
    'dx_cal_bot',
    'resistance_bot'
]


def db_install():
    try:
        conn = psycopg2.connect("dbname=dxbot user=postgres host=localhost")
        cur = conn.cursor()
        cur.execute('SELECT * FROM quotes;')
        conn.close()
    except psycopg2.Error as e:
        print('One of the necessary tables does not exist.')
        exit()


def parse_message(slack_events):
    """
    Parses a list of events coming from the Slack RTM API to find bot commands.
    If a bot command is found, this function retruns a tuple of
    Command, args and channel
    If it is not found, then this function returns None, None
    """
    for event in slack_events:
        if event['type'] == 'message' and 'subtype' not in event:
            global last_event
            prev = last_event
            last_event = event
            command, args = parse_command(event['text'])
            if command:
                return command, args, event['channel'], prev
    return None, None, None, None


def parse_command(message_text):
    """
    Finds a direct mention (a mention that is at the beginning) in message text
    and returns the user ID which was mentioned. If there is no direct mention,
    returns None
    """
    matches = re.search(COMMAND_REGEX, message_text, re.IGNORECASE)
    if matches:
        command = matches.group('command')
        if len(matches.groups()) > 1 and matches.group('message') != '':
            return (command, matches.group('message'))
        return (command, None)
    return (None, None)


def handle_command(command, args, channel, prev):
    """
    Executes bot command if the command is known
    """

    default_response = 'That is not a valid command.'

    response = None
    if command.startswith('quote'):
        if args is not None and len(args.split()) > 1:
            response = addQuote(args, users)
        else:
            response = getQuote(args, users)

    if command.startswith('grab'):
        message = '{} {}'.format(user_map[prev['user']], prev['text'])
        response = addQuote(message, users)

    client.api_call(
        'chat.postMessage',
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":
    db_install()
    if client.rtm_connect(with_team_state=False):
        print('dxbot has connected')
        dxbot_id = client.api_call('auth.test').get('user_id')
        users = [
            member['name']
            for member
            in client.api_call('users.list')['members']
            if member['name'] not in EXCLUSION_LIST
        ]
        user_map = {
            member['id']: member['name']
            for member
            in client.api_call('users.list')['members']
            if member['name'] not in EXCLUSION_LIST
        }
        while True:
            command, args, channel, prev = parse_message(client.rtm_read())
            if command:
                handle_command(command, args, channel, prev)
            time.sleep(READ_DELAY)
