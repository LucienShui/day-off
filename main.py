from flask import Flask, request
from chinese_calendar import is_holiday
from datetime import datetime
import shortuuid
from peewee import DoesNotExist

import re

import peewee

db = peewee.SqliteDatabase('data.db')


class User(peewee.Model):
    username = peewee.CharField(max_length=16, primary_key=True)
    token = peewee.CharField(max_length=22, unique=True)

    class Meta:
        database = db


app = Flask(__name__)

pattern = re.compile(r'^20\d{6}$')


def init():
    db.connect()
    User.create_table()

    user, created = User.get_or_create(username='root', defaults={'username': 'root', 'token': shortuuid.uuid()})
    app.logger.warning(user.token)


init()


def login(username: str) -> (str, int):
    if username != 'root' and (len(username) < 4 or len(username) > 16):
        return 'length of username should greater or equal than 8 and less or equal than 16', 400

    token = request.args.get('token', None)
    if token is None:
        return 'token is required', 401

    try:
        User.get(User.username == username, User.token == token)
    except DoesNotExist:
        return 'authorize failed', 401

    return token, 200


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/register/<string:username>')
def register(username: str):
    message, code = login('root')
    if code != 200:
        return message, code

    user, created = User.get_or_create(username=username, defaults={'username': username, 'token': shortuuid.uuid()})
    if not created:
        return 'username already exists', 409
    return user.token, 200


@app.route('/<string:username>/<string:date>')
def day_off(username: str, date: str) -> (str, int):
    if not pattern.match(date):
        return 'date format error, expect yyyyMMdd', 400

    try:
        date = datetime.strptime(date, '%Y%m%d')
    except ValueError:
        return 'invalid date', 400

    message, code = login(username)
    if code != 200:
        return message, code

    return '1' if is_holiday(date) else '0', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
