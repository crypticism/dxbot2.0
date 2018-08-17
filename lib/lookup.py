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

def getQuoteByLookup(args, users):
    """
    Retrieve a random quote containing a specific word.
    """
    updateUsageCount('Lookup Quote')

    if not re.search('^[\w\s]+$', args):
        return "That's not a safe string. Please try again."

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
        SELECT COUNT(*) FROM quotes WHERE quote ~* '.*\y%s\y.*'
    """ % args

    cur.execute(sql)
    (count,) = cur.fetchone()

    if not count:
        sql = """
            SELECT COUNT(*) FROM quotes WHERE quote ILIKE '%%%s%%'
        """ % args

        cur.execute(sql)
        (count,) = cur.fetchone()

        if not count:
            cur.close()
            return 'No quotes with {} in it'.format(args)

        sql = """
            SELECT *
            FROM quotes
            WHERE quote ILIKE '%%%s%%'
            ORDER BY RANDOM()
            LIMIT 1;
        """ % args

    else:
        sql = """
            SELECT *
            FROM quotes
            WHERE quote ~* '.*\y%s\y.*'
            ORDER BY RANDOM()
            LIMIT 1;
        """ % args

    cur.execute(sql)
    (num, name, quote) = cur.fetchone()
    cur.close()

    return '#{}: {} - "{}"'.format(num, name, quote)


def getLookupCount(args, users):
    """
    Retrieve the count of quotes with a specific word
    """
    updateUsageCount('Lookup Count')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    if not re.search('^[\w\s]+#$', args):
        return "That's not a safe string. Please try again."

    searchString = args.replace('#', '').strip()

    sql = """
        SELECT COUNT(*) FROM quotes WHERE quote ~* '.*\y%s\y.*'
    """ % args

    cur.execute(sql)
    (count,) = cur.fetchone()

    if count:
        cur.close()
        return "There are {} quotes containing {}.".format(count, searchString)
    else:
        sql = """
            SELECT *
            FROM quotes
            WHERE quote ILIKE '%%%s%%'
            ORDER BY RANDOM()
            LIMIT 1;
        """ % args
        cur.execute(sql)
        (count,) = cur.fetchone()
        if count:
            cur.close()
            return "There are {} quotes containing {}.".format(count, searchString)

    cur.close()
    return "There are no quotes with {} in it.".format(searchString)
