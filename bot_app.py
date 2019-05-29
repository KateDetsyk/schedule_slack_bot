import os
from flask import abort, Flask, jsonify, request
import mysql.connector
from datetime import date
import calendar

app = Flask(__name__)


def db():
    """
    Connects to database.
    """
    host = os.environ.get('DB_HOST', 'localhost')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    db = os.environ.get("DB_NAME")

    conn = mysql.connector.connect(host=host, user=user, password=password, database=db)
    return conn


def get_schedule(user):
    """
    Gets information from database.
    """
    day = week_day()
    try:
        conn = db()
        cursor = conn.cursor()

        cursor.execute("select * from heroku_87c90fbf3eab3d6.students WHERE name=%s", (user,))
        student = cursor.fetchone()

        if not student:
            return None

        cohort = student[2]

        cursor.execute("SELECT name, start_time, end_time FROM heroku_87c90fbf3eab3d6.schedules WHERE day_and_week=%s and "
                       "cohort = %s", (day, cohort, ))
        schedule = cursor.fetchall()

        if not schedule:
            return None

    except mysql.connector.Error as error:
        print(error)
        raise
    finally:
        conn.close()
        cursor.close()

    return schedule


def convert(string):
    """
    Convert string with info from slack into dictionary.
    """
    string = string.replace("&", " ").replace("=", " ")
    my_dict = {}
    flag = 1
    word = ''
    keyy = ''
    for i in range(len(string)-1):
        if string[i] != ' ':
            word += string[i]
        else:
            if flag == 1:
                keyy = word
                flag = 2
                word = ''
            else:
                flag = 1
                my_dict[keyy] = word
                word = ''
                keyy = ''

    return my_dict


def is_request_valid(request):
    """
    Validate request.
    """
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


def week_day():
    """
    Returns current day.
    """
    my_date = date.today()
    day = calendar.day_name[my_date.weekday()]
    return day


def massage_maker(lst):
    """
    Make massage with schedule.
    """
    pstr = 'Your schedule for today : \n\n'

    for i in lst:
        for j in i:
            pstr += j
            pstr += " | "

        pstr += '\n'

    return pstr


@app.route('/schedule', methods=['POST'])
def schedule_main():
    info = request.get_data(as_text=True)

    if not is_request_valid(request):
        abort(400)

    info = convert(str(info))
    schedule = get_schedule(info['user_name'])

    if not schedule:
        return jsonify(text='No schedule for today.')

    return jsonify(response_type='in_channel', text=massage_maker(schedule))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
