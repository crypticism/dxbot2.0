import os
import random

import psycopg2

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


def addQuote(args, users):
    """
    Insert a new quote into the database.
    """
    user = args.split()[0]
    message = ' '.join(args.split()[1:])
    if user not in users:
        return '{} is not a valid user.'.format(args)

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()
    sql = "INSERT INTO quotes (name, quote) VALUES (%s, %s);"
    cur.execute(sql, (user, message))
    conn.commit()
    cur.close()
    return 'Quote added.'


def getRandomQuote():
    """
    Retrieve a random quote from the database.
    """
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()

    if count:
        index = random.randint(1, count)

        sql = "SELECT * FROM quotes WHERE id = %s;"
        cur.execute(sql, (index))
        (num, name, quote) = cur.fetchone()
        cur.close()

        return '#{}: {} - "{}"'.format(num, name, quote)
    cur.close()
    return 'There are no quotes.'


def getQuoteByID(args):
    """
    Retrieve a quote by a specific ID.
    """
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()

    if int(args) > count:
        cur.close()
        return 'There aren\'t that many quotes.'

    sql = "SELECT * FROM quotes WHERE id = %s;"

    cur.execute(sql, (args))
    (_, name, quote) = cur.fetchone()
    cur.close()

    return '{} - "{}"'.format(name, quote)


def getQuoteCount():
    """
    Retrieve the number of quotes in the database.
    """
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()
    cur.close()
    return 'There are {} quotes.'.format(count)


def getQuoteByName(args, users):
    """
    Retrieve a random quote from a specific user.
    """
    if args.strip() not in users:
        return '{} is not a valid user.'.format(args)

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = "SELECT * FROM quotes WHERE name = %s;"

    cur.execute(sql, (args))
    quotes = cur.fetchall()

    if not len(quotes):
        cur.close()
        return '{} has no quotes.'.format(args)

    index = random.randint(0, len(quotes) - 1)
    (num, name, quote) = quotes[index]
    cur.close()

    return '#{}: {} - "{}"'.format(num, name, quote)


def getQuote(args, users):
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
        return getQuoteByName(args, users)

    return 'Not implemented yet.'
