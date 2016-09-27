# coding: utf-8
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from redis import Redis


app = Flask(__name__)
db = SQLAlchemy(app)
redis = Redis()

ALARM_NUM = 1000


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False)


class Lottery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reward = db.Column(db.Unicode(64), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)
    publish_time = db.Column(db.DateTime(), nullable=False)
    max_number = db.Column(db.Integer, default=0, nullable=False)


class LotteryWinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lottery_id = db.Column(db.Integer, index=True, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    lottery_number_id = db.Column(db.Integer, index=True, nullable=False)


class LotteryUserNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lottery_id = db.Column(db.Integer, index=True, nullable=False)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    number = db.Column(db.Integer, nullable=False)


class LotteryParam(db.Model):
    date = db.Column(db.Integer, primary_key=True)
    sh_param = db.Column(db.Float, nullable=False)
    sz_param = db.Column(db.Float, nullable=False)


def get_lottery_number(lottery_id):
    """
    根据 lottery_id 从 redis 中获取一个号码, 为了避免没有可用号码时发生阻塞,
    当 redis 中剩余的号码小于某个值时, 则通知生产者生成号码并储存到 redis 中.
    """
    key = 'lottery:%d' % lottery_id
    num = redis.lpop(key)
    if redis.llen(key) < ALARM_NUM:
        awake_producer(lottery_id)
    return num


def init_lottery_number(lottery_id):
    """
    抽奖开始前, 在 redis 中预先存储一部分号码
    """
    awake_producer(lottery_id)


def awake_producer(lottery_id):
    """
    通知生产者产生号码
    redis.rpush('lottery', str(lottery_id))
    """
    redis.rpush('lottery', str(lottery_id))


@app.route('/', methods=['POST'])
def get_num():
    lottery_id = request.values.get('lottery_id')
    user_id = request.values.get('user_id')
    num = get_lottery_number(lottery_id)
    return jsonify({'num': num})


if __name__ == '__main__':
    init_lottery_number(1)
    app.run(debug=True)
