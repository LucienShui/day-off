import re
from datetime import datetime
from functools import wraps
from typing import Callable, Tuple, Any

import peewee
import shortuuid
from chinese_calendar import is_holiday
from flask import Flask, request, jsonify, Response
from peewee import DoesNotExist

db = peewee.SqliteDatabase('data.db')


class User(peewee.Model):
    username = peewee.CharField(max_length=16, primary_key=True)
    token = peewee.CharField(max_length=22, unique=True)

    class Meta:
        database = db


class Calendar(peewee.Model):
    username = peewee.CharField(max_length=16, primary_key=True)
    date = peewee.CharField(max_length=8)
    status = peewee.IntegerField()  # 是否休息，1 休息，0 不休息，-1 作废

    class Meta:
        database = db
        indexes = (
            (('username', 'date'), True),
        )


app = Flask(__name__)

pattern = re.compile(r'^20\d{6}$')


def init():
    db.connect()
    User.create_table()
    Calendar.create_table()

    user, created = User.get_or_create(username='root', defaults={'username': 'root', 'token': shortuuid.uuid()})
    app.logger.warning(user.token)


init()


def error_response(message: str, code: int) -> (Response, int):
    return jsonify({
        'code': code,
        'message': message
    }), code


def login(username: str) -> (str, int):
    if username != 'root' and (len(username) < 4 or len(username) > 16):
        return error_response('length of username should greater or equal than 8 and less or equal than 16', 400)

    token = request.args.get('token', None)
    if token is None:
        return error_response('token is required', 401)

    try:
        User.get(User.username == username, User.token == token)
    except DoesNotExist:
        return error_response('authorize failed', 401)

    return token, 200


def require_login(func: Callable[[str, Any], Tuple[str, int]]):
    @wraps(func)
    def wrapper(*args, **kwargs) -> (str, int):
        username = kwargs['username']
        message, code = login(username)
        if code != 200:
            return message, code
        return func(*args, **kwargs)

    return wrapper


def date_validator(func: Callable[[str, Any], Tuple[Response, int]]):
    @wraps(func)
    def wrapper(*args, **kwargs) -> (Response, int):
        date = kwargs['date']
        if not pattern.match(date):
            return error_response('date format error, expect yyyyMMdd', 400)
        return func(*args, **kwargs)

    return wrapper


@app.route('/api/register/<string:username>')
def register(username: str):
    message, code = login('root')
    if code != 200:
        return message, code

    user, created = User.get_or_create(username=username, defaults={'username': username, 'token': shortuuid.uuid()})
    if not created:
        return error_response('username already exists', 409)
    return {'code': 201, 'message': 'OK', 'token': user.token}, 201


@app.route('/api/<string:username>/<string:date>', methods=['GET'])
@require_login
@date_validator
def day_off(username: str, date: str) -> (str, int):
    try:
        ds = date
        date = datetime.strptime(date, '%Y%m%d')
    except ValueError:
        return error_response('invalid date', 400)

    try:
        calendar = Calendar.get(username=username, date=ds)
        if calendar.status != -1:
            if request.accept_mimetypes.best == 'application/json':
                return jsonify({
                    'code': 200,
                    'message': 'OK',
                    'is_holiday': bool(calendar.status),
                }), 200
            return str(calendar.status), 200
    except DoesNotExist:
        pass

    try:
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({
                'code': 200,
                'message': 'OK',
                'is_holiday': is_holiday(date),
            }), 200
        return '1' if is_holiday(date) else '0', 200
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e),
        }), 500


@app.route('/api/<string:username>/<string:date>/<int:status>', methods=['PUT'])
@require_login
@date_validator
def set_holiday(username: str, date: str, status: int) -> (str, int):
    try:
        calendar, created = Calendar.get_or_create(username=username, date=date, defaults={'date': date})
        if not created and calendar.status != status:
            calendar.status = status
            calendar.save()
    except Exception as e:
        return error_response(str(e), 400)
    return {'code': 200, 'message': 'OK'}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
