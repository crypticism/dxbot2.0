import os
import psycopg2
import re

from lib.usage import updateUsageCount

CONNECT_STRING = 'dbname={} user={} host={} password={}'.format(
    os.getenv('DB_NAME', 'dxbot'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PASS', '')
)


def isInt(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


def addQuote(args, users, user_map):
    """
    Insert a new quote into the database.
    """
    updateUsageCount('Add Quote')

    user = args.split()[0].strip()

    if '<@' in user:
        strippedUser = user[2:-1].strip()
        user = user_map.get(strippedUser, None)
        if user is None:
            return '{} is not a valid user.'.format(args)

    if user not in users:
        return '{} is not a valid user.'.format(args)

    message = ' '.join([
        user_map[arg[2:-1]] if '<@' in arg else arg for arg in args.split()[1:]
    ])

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
        INSERT INTO quotes (name, quote)
        VALUES (%s, %s);
    """

    cur.execute(sql, (user, message))
    conn.commit()
    cur.close()

    return 'Quote added.'


def getRandomQuote():
    """
    Retrieve a random quote from the database.
    """
    updateUsageCount('Get Random Quote')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()

    if count:
        sql = "SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1;"

        cur.execute(sql)
        (num, name, quote) = cur.fetchone()
        cur.close()

        return '#{}: {} - "{}"'.format(num, name, quote)

    cur.close()
    return 'There are no quotes.'


def getQuoteByID(args):
    """
    Retrieve a quote by a specific ID.
    """
    updateUsageCount('Get Quote By ID')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()

    if int(args) > count or (abs(int(args))+1 > count and int(args) < 0):
        cur.close()
        return 'There aren\'t that many quotes.'

    sql = """
        SELECT ID,NAME,QUOTE
        FROM 
        quotes
        WHERE ID = CASE
        WHEN %s > 0 THEN %s
        WHEN %s > (
            SELECT COUNT(*) FROM quotes
        ) THEN '1'ELSE (
            SELECT COUNT(*) + %s FROM quotes
        ) END;
    """

    cur.execute(sql, (args, args, args, args))
    (_, name, quote) = cur.fetchone()
    cur.close()

    return '{} - "{}"'.format(name, quote)


def getQuoteCount():
    """
    Retrieve the number of quotes in the database.
    """
    updateUsageCount('Get Quote Count')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()
    cur.close()

    return 'There are {} quotes.'.format(count)


def getQuoteByName(args, users, user_map):
    """
    Retrieve a random quote from a specific user.
    """
    updateUsageCount('Get Quote By Name')

    user = args.strip()

    if '<@' in user:
        strippedUser = user[2:-1].strip()
        user = user_map.get(strippedUser, None)
        if user is None:
            return '{} is not a valid user.'.format(args)

    if user not in users:
        return '{} is not a valid user.'.format(args)

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
        SELECT COUNT(*) FROM quotes WHERE name = %s;
    """

    cur.execute(sql, (user,))
    (count,) = cur.fetchone()

    if not count:
        cur.close()
        return '{} has no quotes.'.format(user)

    sql = """
        SELECT * FROM quotes WHERE name = %s ORDER BY RANDOM() LIMIT 1;
    """

    cur.execute(sql, (user,))
    (num, name, quote) = cur.fetchone()
    cur.close()

    return '#{}: {} - "{}"'.format(num, name, quote)


def getQuote(args, users, user_map):
    """
    Retrieves quotes from the database based on the type of arg passed in
    No args - retrieves a random quote
    integer - retrieves the quote with that id
    # - retrieves the count of quotes
    string - retrieves a random quote with a username matching that string
    """
    if args is None:
        return getRandomQuote()

    if isInt(args):
        return getQuoteByID(args)

    if args == '#':
        return getQuoteCount()

    if type(args) is str:
        return getQuoteByName(args, users, user_map)

    return 'Not implemented yet.'
