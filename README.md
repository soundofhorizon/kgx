# kgx
魔境です。複数のRedisがひしめいています。

# 各種RedisURLについて
os.environで引っ張ることを想定しています。
1. Redis_URL -> 落札ポイントを保存。 key: f"score-{user_id}", point
2. HEROKU_REDIS_BLACK_URL -> ユーザーのオークションの個数を保存。 key: user_id, count
3. HEROKU_REDIS_ORANGE_URL -> 落札額ランキングを保存。椎名のみ。 key: 1~ , [落札者,落札したもの,落札額,userid], ※1から回してifでFalseになる場所に新しい値を詰め込む。

# コミットルール
始めに英単語1字を付与すること。[ADD] [CHANGE] [DELETE] [Refactor] ここら辺をよく使うかな

# git変更について
ここにマージされたものはそのまま本番環境にリリースされます。そのため、機能単位の変更を入れる場合は!versionの数値を挙げてください。
その際のコミット名は[UPDATE]を付与してください。

# コマンド、変数の命名規則
snakecaseで記載してください。
