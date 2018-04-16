import os

import psycopg2

from .usage import updateUsageCount

CONNECT_STRING = 'dbname={} user={} host={} password={}'.format(
    os.getenv('DB_NAME', 'dxbot'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PASS', '')
)


def getChristian():
    """
    Retrieve a random mcar from the database.
    """
    updateUsageCount('Get Christian')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
        SELECT * FROM christian_mc
        INNER JOIN christian_ar
        ON 1=1
        ORDER BY RANDOM() LIMIT 1;
    """

    cur.execute(sql)
    (mc, ar) = cur.fetchone()
    cur.close()

    return 'Christian is the {} of all of {}'.format(mc, ar)
