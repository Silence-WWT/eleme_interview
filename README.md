# 饿了么 笔试题

## 题目一

饿了么用户在下单完成点评会拿到积分, 积分可以在积分商城消费掉. 目前商城推出了新的抽奖玩法.用户点击「立即抽奖」换取抽奖号, 抽奖号从1开始, 如抽奖号与开奖后的中奖号码一致即为中奖.

以下为某一抽奖的示例:
###########################
**活动奖品：**Apple MacBook Air 13.3英寸笔记本电脑 1台 </br>
**活动时间：**2016年1月18日至2016年1月31日 </br>
**开奖及公布时间：**2016年2月2日 </br>
**活动参与：**用户点击「立即抽奖」换取抽奖号，如抽奖号与开奖后的中奖号码一致即为中奖 </br></br>
说明： 同时有多个奖品提供抽奖， 一个用户对同一奖品可以多次抽奖

抽奖规则:
为了保证抽奖过程公正透明，中奖号码计算规则如下

1. 开奖日收盘时的上证指数 x 收盘时的深证指数 x 10000 =12位数。（指数以证交所公布数字为准）
2. 将此12位数的数字倒序排列后（如首位是0，则直接抹去），再除以开奖截止时间发放的抽奖号总数，得到的余数加1即为本次活动的最终中奖号码。
3. 若您的抽奖号与最终中奖号码完全一致，就可以获得本次活动的大奖！

中奖号码计算示例

* 假设截止到1月31日，总共发放了150000个抽奖号
* 2月2日收盘的上证指数为2894.47，深证指数为9975.42
* 2894.47 x 9975.42 x 10000=288735539274
* 倒序得到数字472935537882
* 除以150000，余数87882，87882＋1＝87883
* 所以本次活动中奖号码为87883

简单来说！获得抽奖码越多中奖概率越大哦，快去获取抽奖号吧！</span>
###########################
请给出实现该抽奖的设计和实现思路, 数据库表(包括索引)需要给出详细的设计

### 解答

本题的抽奖方式要求抽奖号码是连续自增的, 应避免 抽奖号码不连续导致某号码无对应的中奖用户, 抽奖号码重复导致有多个中奖用户 的情况发生.抽奖号码若依赖 MySQL 主键自增, 插入新数据时需要锁表会带来较大性能开销, 并发时也可能有 id 重复的情况发生.

所以我认为这个问题的关键是需要实现一个 id 生成器. 分布式全局生成器很难保证 id 的连续性, 所以本题采用单点的生成器. 

我在本题中通过 Redis 阻塞队列实现了消息传递. 单进程的生产者通过阻塞方法 blpop 监听事件, 当获取到事件时, 生成一批 id 存储在 Redis 中, 并更新 MySQL 中该奖品的最大抽奖号码. 为了避免后端程序获取 id 时发现 id 已耗尽而导致阻塞, 每次获取 id 时都会对剩余 id 数量进行判断, 若数量小于警告值, 则唤醒生产者. 并发情况下可能会同时多次唤醒生产者, 所以生产者也需要判断 id 数量是否小于临界值.

### 数据库设计

```sql
-- 用户
CREATE TABLE `user` (
	`id` int(11) NOT NULL ,
	`name` varchar(64) NOT NULL,
	PRIMARY KEY (`id`),
);

-- 奖品
CREATE TABLE `lottery` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `reward` varchar(64) NOT NULL,
    `start_time` datetime NOT NULL,
    `end_time` datetime NOT NULL,
    `publish_time` datetime NOT NULL,
    `max_number` int(11) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
);

-- 获奖记录
CREATE TABLE `lottery_winner` (
	`lottery_id` int(11) NOT NULL,
	`number` int(11) NOT NULL,
	`date` date NOT NULL,
	`sh_param` float NOT NULL,
	`sz_param` float NOT NULL,
	PRIMARY KEY (`lottery_id`),
);

-- 用户获奖号码
CREATE TABLE `lottery_user_number` (
	`lottery_id` int(11) NOT NULL,
	`number` int(11) NOT NULL,
	`user_id` int(11) NOT NULL,
	`create_time` datetime NOT NULL,
	PRIMARY KEY (`lottery_id`, `number`),
);
```

表 `lottery_user_number` 使用了复合主键, 能确保了每个奖品获奖号码的唯一性.

### 可能存在的问题

+ Redis 故障
  + Redis 主从模式 + Keepalive + VIP. 但这种方案仍然可能导致丢失数据. Master 发生宕机, 但数据未完全同步至 Slave, 此时将 Slave 提升为 Master, 会导致同步未完成的数据丢失.
  + 双主复制 
+ MySQL 故障
  + 双主复制
+ 恶意用户大量请求或流量峰值来临, 生产者来不及生产足够多的 id
  + 增大唤醒生产者的临界值
  + 将 id 生成器作为独立的服务(包括生产者和消费者), 并使用令牌桶算法进行限流

## 题目二

在试题一的基础上，产品经理提了个新需求，要展示你的抽奖次数超过 百分之多少的人

示例：一个奖品有9个人抽，其中一个人抽了3次， 其他8个人抽了1次。 此时用户A抽了1次，会向他展示他的抽奖次数超过了 0 %的人， 又抽了一次展示 8/(9+1) = 80% （此数据准确性要求不高）

### 解答

新建如下数据表

```sql
-- 每个奖品用户抽奖次数统计
CREATE TABLE `lottery_user_count` (
	`lottery_id` int(11) NOT NULL,
	`user_id` int(11) NOT NULL,
	`count` int(11) NOT NULL,
	PRIMARY KEY (`lottery_id`, `user_id`),
);
```

可以通过如下语句查询, 获得每个抽奖次数的用户人数, 并计算得出每个抽奖次数超过了多少用户的数据, 因为这个需求对数据的准确性要求不高, 可以用脚本定期执行, 并将结果存储在 Redis 中, 用户请求时, 从 Redis 中获取已经计算的数据.

```sql
SELECT COUNT(*) 
FROM lottery_user_count
WHERE lottery_id = 123456
GROUP BY count;
```
