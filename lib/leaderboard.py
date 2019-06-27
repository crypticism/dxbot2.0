import os
import psycopg2

from lib.usage import updateUsageCount

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

    sql = "SELECT count FROM leaderboard WHERE name = %s AND count IS NOT NULL;"

    cur.execute(sql, (user,))
    if cur.rowcount > 0:
        (count,) = cur.fetchone()
    
    if count is not None:
        count = count + 1
        sql = """
          UPDATE leaderboard
          SET count = count + 1
          WHERE name = %s;
        """
    else:
        count = 1
        sql = """
        INSERT INTO leaderboard
        (name, count)
        VALUES (%s, 1)
        """

    cur.execute(sql, (user,))

    conn.commit()
    cur.close()

    return '{}\'s score is {}'.format(user, count)


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
      SELECT count FROM leaderboard WHERE name = %s AND count IS NOT NULL;
    """

    cur.execute(sql, (user,))
    if cur.rowcount > 0:
        (count,) = cur.fetchone()

    if count is not None:
        count = count - 1
        sql = """
          UPDATE leaderboard
          SET count = count - 1
          WHERE name = %s;
        """
    else:
        count = -1
        sql = """
        INSERT INTO leaderboard
        (name, count)
        VALUES (%s, -1);
        """

    conn.commit()
    cur.close()

    return '{}\'s score is {}'.format(user, count)


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
