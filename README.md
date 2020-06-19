# kgx
魔境です。<br>Postgre SQL 12.3によりデータベースの管理がされています。

# 各種DBのテーブル、カラムについて
> auction
>
>> ch_id: チャンネルID格納. bigint. unique key<br>
>> auction_owner_id: そのチャンネルにおけるオークションのオーナーのid. bigint<br>
>> auction_item: そのチャンネルの出品物. text<br>
>> auction_start_price: text<br>
>> auction_bin_time: text<br>
>> auction_end_time: 終了時刻がdatetime型で入る。 text <br>
>> unit: 単位. text<br>
>
> deal
>
>> ch_id: チャンネルID格納. bigint. unique key<br>
>> deal_owner_id: そのチャンネルにおけるオークションのオーナーのid. bigint<br>
>> deal_item: そのチャンネルの出品物. text<br>
>> deal_hope_price: text<br>
>> deal_end_time: 終了時刻がdatetime型で入る。 text <br>
>> unit: 単位. text<br>
>
> bid_ranking
>
>> bidder_name: 落札者の名前 text<br>
>> item_name: 出品物の名前 text<br>
>> bid_price 落札額 bigint(shortintの方が10倍マシ)<br>
>> seller_id: ※ idと言っておきながら格納されているのはニックネーム。seller_nameにするべき text<br>
>
> user_data
>
>> user_id: 参加時のmcid認証が通ると登録される。 bigint unique key<br>
>> bid_score: 落札ポイントを格納。 smallint(3万以上とか考慮してない)<br>
>> warn_level: 警告レベルを格納。 smallint(0-3以外を取らない変数のため要求を満たす)<br>


# コミットルール
始めに英単語1字を付与すること。[ADD] [CHANGE] [DELETE] [Refactor] ここら辺をよく使うかな

# git変更について
ここにマージされたものはそのまま本番環境にリリースされます。そのため、機能単位の変更を入れる場合は!versionの数値を挙げてください。
その際のコミット名は[UPDATE]を付与してください。

# コマンド、変数の命名規則
snake_caseで記載してください。
