import psycopg2

import os

from .usage import updateUsageCount

CONNECT_STRING = 'dbname={} user={} host={} password={}'.format(
    os.getenv('DB_NAME', 'dxbot'),
    os.getenv('DB_USER', 'postgres'),
    os.getenv('DB_HOST', 'localhost'),
    os.getenv('DB_PASS', '')
)


def incrementUser(args, users, user_map):
    """
    Increment a users score.
    """
    user = args.split()[0].strip()

    if '<@' in user:
        strippedUser = user[2:-1].strip()
        user = user_map.get(strippedUser, None)
        if user is None:
            return '{} is not a valid user.'.format(args)

    if user not in users:
        return '{} is not a valid user.'.format(args)

    updateUsageCount('Increment User')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = "SELECT COUNT(*) FROM leaderboard WHERE name = '%s';" % user

    cur.execute(sql)
    (count,) = cur.fetchone()

    if count:
        sql = """
          UPDATE leaderboard
          SET count = count + 1
          WHERE name = '%s';
        """ % user
    else:
        sql = """
        INSERT INTO leaderboard
        (name, count)
        VALUES ('%s', 1)
        """ % user

    cur.execute(sql)

    sql = """
      SELECT name, count FROM leaderboard WHERE name = '%s';
    """ % user

    cur.execute(sql)
    (name, count) = cur.fetchone()

    conn.commit()
    cur.close()

    return '{}\'s score is {}'.format(name, count)


def decrementUser(args, users, user_map):
    """
    Decrement a users score.
    """
    user = args.split()[0].strip()

    if '<@' in user:
        strippedUser = user[2:-1].strip()
        user = user_map.get(strippedUser, None)
        if user is None:
            return '{} is not a valid user.'.format(args)

    if user not in users:
        return '{} is not a valid user.'.format(args)

    updateUsageCount('Decrement User')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = """
      SELECT COUNT(*) FROM leaderboard WHERE name = '%s';
    """ % user

    cur.execute(sql)
    (count,) = cur.fetchone()

    if count:
        sql = """
          UPDATE leaderboard
          SET count = count - 1
          WHERE name = '%s';
        """ % user
    else:
        sql = """
        INSERT INTO leaderboard
        (name, count)
        VALUES ('%s', -1);
        """ % user

    cur.execute(sql)

    sql = """
      SELECT name, count FROM leaderboard WHERE name = '%s';
    """ % user

    cur.execute(sql)
    (name, count) = cur.fetchone()

    conn.commit()
    cur.close()

    return '{}\'s score is {}'.format(name, count)


def getLeaderboard():
    """
    Print off the current leaderboard.
    """
    updateUsageCount('Get Leaderboard')

    conn = psycopg2.connect(CONNECT_STRING)
    cur = conn.cursor()

    sql = "SELECT name, count FROM leaderboard;"

    cur.execute(sql)

    stats = cur.fetchall()

    if not len(stats):
        return "No users have been rated yet."

    stat_strings = ['{}: {}'.format(name, count) for (name, count) in stats]

    return "```{}```".format('\n'.join(stat_strings))
