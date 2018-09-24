import os
import time
import re

import emoji

import psycopg2
from slackclient import SlackClient

from lib.leaderboard import decrementUser, getLeaderboard, incrementUser
from lib.lookup import getLookupCount, getQuoteByLookup, getLookupCountExact, getQuoteByLookupExact
from lib.mcar import getChristian
from lib.quote import addQuote, getQuote
from lib.usage import getUsageCounts

# Create client
client = SlackClient(os.environ.get('DXBOT_TOKEN'))
# User ID: Set after connecting
dxbot_id = None
users = []
user_map = {}
last_event = None

# Constants
READ_DELAY = 1  # 1 second read delay
COMMAND_CHARACTER = os.getenv('COMMAND_CHARACTER', '!')
COMMAND_REGEX = r"^" + re.escape(COMMAND_CHARACTER) + \
    r"(?P<command>[\w+-]+) ?(?P<message>.*)?$"
CONNECT_STRING = 'dbname={} user={} host={} password={}'.format(
    os.getenv('DB_NAME', 'dxbot'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PASS', '')
)

EXCLUSION_LIST = [
    'slackbot',
    'scryfall',
    'dx_bot',
    'dx_cal_bot',
    'resistance_bot'
]

def refresh_users():
    global users
    global user_map
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

def spongeify(message):
    responge = '^([\w\-]+ )(.*)'
    match = re.search(responge, message)
    u_temp = match.group(1)
    m_temp = match.group(2)
    sponge = [_.lower() if i % 2 == 0 else _.upper()
        for i, _
        in enumerate(char for char in m_temp if char.isalpha())
    ]
    [sponge.insert(*_) for _ in
        [(i, char) for i, char in enumerate(m_temp) if not char.isalpha()]
    ]
    return u_temp+''.join(sponge)

def pastafy(message):
	emoji = client.api_call('emoji.list')['emoji']
	custom_emoji_list = emoji.keys()
	
	regetti = '^([\w\-]+ )(.*)'
	match = re.search(regetti, message)
	u_temp = match.group(1)
	m_temp = match.group(2)

	pasta = m_temp.split()
	for index, noodle in enumerate(pasta):
		if noodle.count(':') > 1:
			splitnoodle = noodle.split(':')
			for findex, grain in enumerate(splitnoodle):
				if grain:
					couldbemoji = ':{}:'.format(grain)
					if couldbemoji in emoji.EMOJI_ALIAS_UNICODE or couldbemoji in custom_emoji_list:
						splitnoodle[findex] = (grain+couldbemoji)
			pasta[index] = ('').join(splitnoodle)
		else:
			couldbemoji = ':{}:'.format(noodle)
			if couldbemoji in emoji.EMOJI_ALIAS_UNICODE or couldbemoji in custom_emoji_list:
				pasta[index] = (noodle+couldbemoji)
	return u_temp+' '.join(pasta)
	
def db_install():
    try:
        conn = psycopg2.connect(CONNECT_STRING)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM quotes;')
        cur.execute('SELECT COUNT(*) FROM usage;')
        cur.execute('SELECT COUNT(*) FROM leaderboard')
        cur.execute('SELECT COUNT(*) FROM christian_mc')
        cur.execute('SELECT COUNT(*) FROM christian_ar')
        cur.close()
    except psycopg2.Error as e:
        if e and e.pgerror and 'does not exist' in e.pgerror:
            conn = psycopg2.connect(CONNECT_STRING)
            cur = conn.cursor()
            if 'quotes' in e.pgerror:
                cur.execute(
                    """
                    CREATE TABLE quotes(
                        id      SERIAL          PRIMARY KEY,
                        name    VARCHAR(50)     NOT NULL,
                        quote   VARCHAR(2000)   NOT NULL
                    );
                    """
                )

            if 'usage' in e.pgerror:
                cur.execute(
                    """
                    CREATE TABLE usage(
                        id          SERIAL      PRIMARY KEY,
                        function    VARCHAR(50) NOT NULL,
                        count       INTEGER     NOT NULL
                    );
                    """
                )

            if 'leaderboard' in e.pgerror:
                cur.execute(
                    """
                    CREATE TABLE leaderboard(
                        id      SERIAL      PRIMARY KEY,
                        name    VARCHAR(50) NOT NULL,
                        count   INTEGER     NOT NULL
                    );
                    """
                )

            if 'christian_ar' in e.pgerror:
                cur.execute(
                    """
                    CREATE TABLE christian_ar(
                        id VARCHAR(300) NOT NULL
                    );
                    """
                )

            if 'christian_mc' in e.pgerror:
                cur.execute(
                    """
                    CREATE TABLE christian_mc(
                        id VARCHAR(300) NOT NULL
                    );
                    """
                )

            conn.commit()
            cur.close()
        else:
            print('Error connecting to database.')
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
            last_event = event if not \
                event['text'].startswith(COMMAND_CHARACTER) else last_event
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

    refresh_users()

    response = None
    if command.startswith('quote'):
        if args is not None and len(args.split()) > 1:
            response = addQuote(args, users, user_map)
        else:
            response = getQuote(args, users, user_map)

    if command.startswith('lookup'):
        if args is not None:
            if re.search('^[\w\s]+#$', args):
                response = getLookupCount(args, users)
            else:
                response = getQuoteByLookup(args, users)
        else:
            response = 'No arguments provided'

    if command.startswith('elookup'):
        if args is not None:
            if re.search('^[\w\s]+#$', args):
                response = getLookupCountExact(args, users)
            else:
                response = getQuoteByLookupExact(args, users)
        else:
            response = 'No arguments provided'

    if command.startswith(('grab','yoink','snag','slurp')):
        message = '{} {}'.format(user_map[prev['user']], prev['text'])
        if command.startswith('yoink'):
            message = spongeify(message)
		if command.startswith('slurp'):
			message = pastafy(message)

        response = addQuote(message, users, user_map)

    if command.startswith('usage'):
        response = getUsageCounts()

    if command.startswith('++'):
        if args is not None:
            response = incrementUser(args, users, user_map)
        else:
            response = 'Specify a user.'

    if command.startswith('--'):
        if args is not None:
            response = decrementUser(args, users, user_map)
        else:
            response = 'Specify a user'

    if command.startswith('leaderboard'):
        response = getLeaderboard()
    if command.startswith('christian'):
        response = getChristian()
    if (command[0].isdigit() and command):
        return

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
        refresh_users()
        while True:
            command, args, channel, prev = parse_message(client.rtm_read())
            if command:
                handle_command(command, args, channel, prev)
            time.sleep(READ_DELAY)
