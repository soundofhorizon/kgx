# kgx
魔境です。複数のRedisがひしめいています。

# 各種RedisURLについて
os.environで引っ張ることを想定しています。
Redis_URL -> 落札ポイントを保存。 key:f"score-{user_id}", point
HEROKU_REDIS_BLACK_URL -> ユーザーのオークションの個数を保存。 key: user_id, count
HEROKU_REDIS_ORANGE_URL -> 落札額ランキングを保存。椎名のみ。 key: 1~ , [落札者,落札したもの,落札額,userid], ※1から回してifでFalseになる場所に新しい値を詰め込む。
