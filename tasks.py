# coding: utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from redis import Redis

ALARM_NUM = 1000


class Producer:
    def __init__(self):
        self.redis = Redis()
        self.app = Flask('task')
        self.db = SQLAlchemy(self.app)

    def produce(self):
        """
        redis.blpop 会从列表开头获取一个元素, 如果列表是空, 则会阻塞
        生产者获取到 Lottery 对象后, 根据该对象的 max_number 生成一定数量的号码, 存入 redis 并更新 max_number
        因为并发的时候可能会同时多次唤醒生产者, 所以这里需要重新判断是否小于 ALARM_NUM
        """
        with self.app.app_context():
            while True:
                lottery_id = self.redis.blpop('lottery')[1]
                key = 'lottery:%d' % lottery_id
                if self.redis.llen(key) < ALARM_NUM:  # 并发时可能会多次唤醒
                    # 生成新的号码并更新, 通过 self.redis.rpush 推入新生成的号码, 并更新 max_number
                    pass


if __name__ == '__main__':
    Producer().produce()
