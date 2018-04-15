import random

import psycopg2


def isInt(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


def addQuote(args, users):
    return 'Not implemented yet.'


def getQuote(args, users):
    """
    Retrieves quotes from the database based on the type of arg passed in
    No args - retrieves a random quote
    integer - retrieves the quote with that id
    # - retrieves the count of quotes
    string - retrieves a random quote with a username matching that string
    """
    conn = psycopg2.connect("dbname=dxbot user=postgres host=localhost")
    cur = conn.cursor()
    if args is None:
        cur.execute('SELECT COUNT(*) FROM quotes;')
        (count,) = cur.fetchone()
        if count:
            index = random.randint(1, count)
            cur.execute('SELECT * FROM quotes WHERE id = {};'.format(index))
            (num, name, quote) = cur.fetchone()
            cur.close()
            return '#{}: {} - "{}"'.format(num, name, quote)
        cur.close()
        return 'There are no quotes.'

    if isInt(args):
        cur.execute('SELECT COUNT(*) FROM quotes;')
        (count,) = cur.fetchone()
        if int(args) > count:
            cur.close()
            return 'There aren\'t that many quotes.'

        cur.execute('SELECT * FROM quotes WHERE id = {};'.format(args))
        (_, name, quote) = cur.fetchone()
        cur.close()
        return '{} - "{}"'.format(name, quote)

    if args == '#':
        cur.execute('SELECT COUNT(*) FROM quotes;')
        (count,) = cur.fetchone()
        cur.close()
        return 'There are {} quotes.'.format(count)

    if type(args) is str:
        if args.strip() in users:
            cur.execute('SELECT * FROM quotes WHERE name = \'{}\';'.format(args))
            quotes = cur.fetchall()
            if not len(quotes):
                cur.close()
                return '{} has no quotes.'.format(args)

            index = random.randint(0, len(quotes) - 1)
            (num, name, quote) = quotes[index]
            cur.close()
            return '#{}: {} - "{}"'.format(num, name, quote)
        else:
            cur.close()
            return '{} is not a valid user.'.format(args)

    cur.close()
    return 'Not implemented yet.'
