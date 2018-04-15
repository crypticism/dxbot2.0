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
    sql = "INSERT INTO quotes (name, quote) VALUES (%s, %s);" % (str(user), str(message))
    cur.execute(sql)
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
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM quotes;')
    (count,) = cur.fetchone()

    if int(args) > count:
        cur.close()
        return 'There aren\'t that many quotes.'

    sql = """
        SELECT ID,NAME,QUOTE
        FROM (
            SELECT row_number() OVER (ORDER BY id asc) AS roww, * FROM quotes
        ) a
        WHERE roww = CASE
        WHEN '%s' > 0 THEN '%s'
        WHEN '%s' > (
            SELECT COUNT(*) FROM quotes
        ) THEN '1'ELSE (
            SELECT COUNT(*) + '%s' FROM quotes
        ) END;
    """ % (str(args),str(args),str(args),str(args))

    cur.execute(sql)
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

    sql = "SELECT COUNT(*) FROM quotes WHERE name = '%s';" % str(args)

    cur.execute(sql)
    (count,) = cur.fetchone()

    if not count:
        cur.close()
        return '{} has no quotes.'.format(args)

    sql = """
        SELECT * FROM quotes WHERE name = '%s' ORDER BY RANDOM() LIMIT 1;
    """ % str(args)

    cur.execute(sql)
    (num, name, quote) = cur.fetchone()
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


def getQuoteByLookup(args, users):
    """
    Retrieve a random quote containing a specific word.
    """

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
        SELECT COUNT(*) FROM quotes WHERE quote ILIKE '%%%s%%';
    """ % str(args)

    cur.execute(sql)
    (count,) = cur.fetchone()

    if not count:
        cur.close()
        return 'No quotes with {} in it'.format(args)

    sql = """
        SELECT *
        FROM quotes
        WHERE quote
        ILIKE '%%%s%%'
        ORDER BY RANDOM()
        LIMIT 1;
    """ % str(args)

    cur.execute(sql)
    (num, name, quote) = cur.fetchone()
    cur.close()

    return '#{}: {} - "{}"'.format(num, name, quote)
