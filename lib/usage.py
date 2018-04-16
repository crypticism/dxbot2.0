import psycopg2

import os

CONNECT_STRING = 'dbname={} user={} host={} password={}'.format(
    os.getenv('DB_NAME', 'dxbot'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PASS', '')
)


def updateUsageCount(functionName):
    """
    Increment the usage count for a specific function
    """
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = "SELECT COUNT(*) FROM usage WHERE function = '%s'" % functionName

    cur.execute(sql)
    (count,) = cur.fetchone()

    if count:
        sql = """
          UPDATE usage
          SET count = count + 1
          WHERE function = '%s';
        """ % functionName
    else:
        sql = """
        INSERT INTO usage
        (function, count)
        VALUES ('%s', 1)
        """ % functionName

    cur.execute(sql)
    conn.commit()
    cur.close()


def getUsageCounts():
    """
    Retrieve the usage counts for all functions
    """
    updateUsageCount('Get Usage Counts')
    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = "SELECT function, count FROM usage;"

    cur.execute(sql)

    usages = cur.fetchall()

    if not len(usages):
        return "No functions have been called yet."

    usage_strings = ['{}: {}'.format(func, count) for (func, count) in usages]

    return "```{}```".format('\n'.join(usage_strings))
