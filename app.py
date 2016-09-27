# coding: utf-8
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from redis import Redis


app = Flask(__name__)
db = SQLAlchemy(app)
redis = Redis()

ALARM_NUM = 1000


class User(db.Model):
    """
    用户
    """
    # id
    id = db.Column(db.Integer, primary_key=True)
    # 用户昵称
    name = db.Column(db.Unicode(64), nullable=False)


class Lottery(db.Model):
    """
    奖品
    """
    # id
    id = db.Column(db.Integer, primary_key=True)
    # 奖励名称
    reward = db.Column(db.Unicode(64), nullable=False)
    # 开始时间
    start_time = db.Column(db.DateTime(), nullable=False)
    # 结束时间
    end_time = db.Column(db.DateTime(), nullable=False)
    # 公开抽奖时间
    publish_time = db.Column(db.DateTime(), nullable=False)
    # 最大抽奖号码
    max_number = db.Column(db.Integer, default=0, nullable=False)


class LotteryWinner(db.Model):
    """
    中奖者
    """
    # 抽奖活动 id
    lottery_id = db.Column(db.Integer, primary_key=True)
    # 中奖号码
    number = db.Column(db.Integer, nullable=False)
    # 数据日期
    date = db.Column(db.Date(), nullable=False)
    # 上证指数
    sh_param = db.Column(db.Float, nullable=False)
    # 深证指数
    sz_param = db.Column(db.Float, nullable=False)


class LotteryUserNumber(db.Model):
    """
    用户抽奖号码记录
    """
    # 奖品 id
    lottery_id = db.Column(db.Integer, nullable=False, primary_key=True)
    # 抽奖号码
    number = db.Column(db.Integer, nullable=False, primary_key=True)
    # 用户 id
    user_id = db.Column(db.Integer, index=True, nullable=False)
    # 时间
    create_time = db.Column(db.DateTime(), nullable=False)


class LotteryUserCount(db.Model):
    """
    记录某用户在某抽奖活动中的抽奖次数
    """
    # 奖品 id
    lottery_id = db.Column(db.Integer, primary_key=True)
    # 用户 id
    user_id = db.Column(db.Integer, primary_key=True)
    # 抽奖次数
    count = db.Column(db.Integer, nullable=False)


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
    """
    redis.rpush('lottery', str(lottery_id))


@app.route('/', methods=['POST'])
def get_num():
    """
    获取 lottery_id, user_id 与 num, 并添加记录
    """
    lottery_id = request.values.get('lottery_id')
    user_id = request.values.get('user_id')
    num = get_lottery_number(lottery_id)
    # 添加 LotteryUserNumber 记录
    return jsonify({'num': num})


if __name__ == '__main__':
    init_lottery_number(1)
    app.run(debug=True)
