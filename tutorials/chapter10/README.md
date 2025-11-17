# 第10章: イベントシステム

## 学習目標
- SQLAlchemyのイベントシステムを理解する
- ORMイベント（before_insert, after_updateなど）の使い方を学ぶ
- コネクションイベントとプールイベントを活用する
- カスタムロジックをイベントハンドラーで実装する

## イベントシステムとは

SQLAlchemyのイベントシステムは、データベース操作の各段階でカスタムコードを実行できる強力な機能です。

### イベントの種類

```
┌─────────────────────────────────┐
│ ORMイベント                     │
│  ├ before_insert                │
│  ├ after_insert                 │
│  ├ before_update                │
│  ├ after_update                 │
│  ├ before_delete                │
│  ├ after_delete                 │
│  └ before_flush, after_flush    │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ セッションイベント              │
│  ├ after_transaction_create     │
│  ├ after_commit                 │
│  ├ after_rollback               │
│  └ persistent_to_deleted        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ コネクションイベント            │
│  ├ before_cursor_execute        │
│  ├ after_cursor_execute         │
│  ├ connect                      │
│  └ checkout                     │
└─────────────────────────────────┘
```

## ORMイベント

### before_insert / after_insert

```python
from sqlalchemy import event
from datetime import datetime

class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column()
    view_count: Mapped[int] = mapped_column(default=0)

@event.listens_for(Article, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """挿入前のイベント"""
    # slugを自動生成
    if not target.slug:
        target.slug = target.title.lower().replace(' ', '-')

    # タイムスタンプを自動設定
    target.created_at = datetime.utcnow()

    print(f"挿入前: {target.title}")

@event.listens_for(Article, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """挿入後のイベント"""
    print(f"挿入完了: ID={target.id}")

# 使用例
with Session(engine) as session:
    article = Article(title="Hello World")
    session.add(article)
    session.commit()
    # 出力:
    # 挿入前: Hello World
    # 挿入完了: ID=1
    # article.slug == "hello-world"
```

### before_update / after_update

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column()
    version: Mapped[int] = mapped_column(default=0)

@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    """更新前のイベント"""
    # 更新日時を自動更新
    target.updated_at = datetime.utcnow()

    # バージョン番号をインクリメント（楽観的ロック）
    target.version += 1

    print(f"更新前: {target.name}, version={target.version}")

@event.listens_for(User, 'after_update')
def receive_after_update(mapper, connection, target):
    """更新後のイベント"""
    print(f"更新完了: {target.name}")
```

### before_delete / after_delete

```python
class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    is_deleted: Mapped[bool] = mapped_column(default=False)

@event.listens_for(Post, 'before_delete')
def receive_before_delete(mapper, connection, target):
    """削除前のイベント"""
    print(f"削除予定: {target.title}")

    # 論理削除に変更（実際には削除しない）
    target.is_deleted = True
    session = object_session(target)
    session.add(target)

@event.listens_for(Post, 'after_delete')
def receive_after_delete(mapper, connection, target):
    """削除後のイベント"""
    print(f"削除完了: {target.title}")
```

## Flushイベント

Flushは、セッションの変更をデータベースに同期するタイミングです。

```python
@event.listens_for(Session, 'before_flush')
def receive_before_flush(session, flush_context, instances):
    """Flush前のイベント"""
    print(f"Flush開始: {len(session.new)}個の新規オブジェクト")
    print(f"         {len(session.dirty)}個の変更オブジェクト")
    print(f"         {len(session.deleted)}個の削除オブジェクト")

    # 全ての新規ユーザーに処理を適用
    for obj in session.new:
        if isinstance(obj, User):
            obj.created_at = datetime.utcnow()

@event.listens_for(Session, 'after_flush')
def receive_after_flush(session, flush_context):
    """Flush後のイベント"""
    print("Flush完了")
```

## 属性変更イベント

特定の属性が変更されたときにイベントを発火させます。

```python
from sqlalchemy.orm import attributes

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[Decimal]
    discount_price: Mapped[Optional[Decimal]]

@event.listens_for(Product.price, 'set')
def receive_price_set(target, value, oldvalue, initiator):
    """価格が変更されたとき"""
    print(f"価格変更: {oldvalue} → {value}")

    # 割引価格が正価格を超えないようにバリデーション
    if target.discount_price and value < target.discount_price:
        raise ValueError("割引価格は正価格以下である必要があります")

@event.listens_for(Product.discount_price, 'set')
def receive_discount_set(target, value, oldvalue, initiator):
    """割引価格が設定されたとき"""
    if value and target.price < value:
        raise ValueError("割引価格は正価格以下である必要があります")
```

## コネクションイベント

### クエリロギング

```python
import logging

logger = logging.getLogger('sqlalchemy.engine')

@event.listens_for(Engine, 'before_cursor_execute')
def receive_before_cursor_execute(conn, cursor, statement,
                                   parameters, context, executemany):
    """クエリ実行前"""
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.debug(f"クエリ開始: {statement[:50]}...")

@event.listens_for(Engine, 'after_cursor_execute')
def receive_after_cursor_execute(conn, cursor, statement,
                                  parameters, context, executemany):
    """クエリ実行後"""
    total = time.time() - conn.info['query_start_time'].pop()
    logger.debug(f"クエリ完了: {total:.4f}秒")

    # 遅いクエリを警告
    if total > 1.0:
        logger.warning(f"遅いクエリ検出 ({total:.2f}秒): {statement[:100]}")
```

### 接続時の初期化

```python
@event.listens_for(Engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    """新しい接続が確立されたとき"""
    print("新しいDB接続を確立")

    # PostgreSQLの場合、タイムゾーンを設定
    if 'postgresql' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET timezone='UTC'")
        cursor.close()

@event.listens_for(Engine, 'checkout')
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """プールから接続を取り出したとき"""
    print("接続をプールから取得")
```

## プールイベント

```python
@event.listens_for(QueuePool, 'connect')
def receive_pool_connect(dbapi_conn, connection_record):
    """プールが新しい接続を作成したとき"""
    print("プールに新しい接続を追加")

@event.listens_for(QueuePool, 'checkin')
def receive_pool_checkin(dbapi_conn, connection_record):
    """接続がプールに返却されたとき"""
    print("接続をプールに返却")

@event.listens_for(QueuePool, 'checkout')
def receive_pool_checkout(dbapi_conn, connection_record, connection_proxy):
    """プールから接続を取得したとき"""
    print("プールから接続を取得")
```

## 実践例: 監査ログシステム

```python
class AuditLog(Base):
    """監査ログテーブル"""
    __tablename__ = 'audit_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(50))
    record_id: Mapped[int]
    action: Mapped[str] = mapped_column(String(10))  # INSERT/UPDATE/DELETE
    old_values: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    new_values: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    user_id: Mapped[Optional[int]]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)

import json
from sqlalchemy.orm import object_session

def create_audit_listeners(model_class):
    """任意のモデルに監査ログを追加"""

    @event.listens_for(model_class, 'after_insert')
    def after_insert(mapper, connection, target):
        session = object_session(target)
        log = AuditLog(
            table_name=model_class.__tablename__,
            record_id=target.id,
            action='INSERT',
            new_values=json.dumps(dict(target))
        )
        session.add(log)

    @event.listens_for(model_class, 'after_update')
    def after_update(mapper, connection, target):
        session = object_session(target)
        log = AuditLog(
            table_name=model_class.__tablename__,
            record_id=target.id,
            action='UPDATE',
            new_values=json.dumps(dict(target))
        )
        session.add(log)

    @event.listens_for(model_class, 'after_delete')
    def after_delete(mapper, connection, target):
        session = object_session(target)
        log = AuditLog(
            table_name=model_class.__tablename__,
            record_id=target.id,
            action='DELETE',
            old_values=json.dumps(dict(target))
        )
        session.add(log)

# 監査対象のモデルに適用
create_audit_listeners(User)
create_audit_listeners(Product)
```

## イベントの削除

```python
# イベントリスナーを削除
@event.listens_for(User, 'before_insert')
def my_listener(mapper, connection, target):
    print("before insert")

# 後で削除
event.remove(User, 'before_insert', my_listener)
```

## once=Trueオプション

```python
@event.listens_for(User, 'before_insert', once=True)
def one_time_listener(mapper, connection, target):
    """1回だけ実行される"""
    print("初回のみ実行")
```

## propagate=True

継承されたクラスにもイベントを伝播させます。

```python
@event.listens_for(Base, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    """全てのモデルのINSERT前に実行"""
    print(f"挿入: {target.__class__.__name__}")
```

## ベストプラクティス

### 1. イベント内で例外を発生させない

```python
# ❌ 悪い例
@event.listens_for(User, 'before_insert')
def bad_listener(mapper, connection, target):
    if not validate(target):
        raise ValueError("Invalid data")  # NG: トランザクションが壊れる

# ✅ 良い例: バリデーションは事前に
def create_user(name, email):
    if not validate_email(email):
        raise ValueError("Invalid email")
    user = User(name=name, email=email)
    session.add(user)
```

### 2. イベント内でセッションを直接操作しない

```python
# ❌ 悪い例
@event.listens_for(User, 'after_insert')
def bad_listener(mapper, connection, target):
    session.add(AnotherModel())  # NG

# ✅ 良い例: connectionを使う
@event.listens_for(User, 'after_insert')
def good_listener(mapper, connection, target):
    connection.execute(
        insert(AnotherModel).values(...)
    )
```

### 3. パフォーマンスに注意

```python
# ❌ 重い処理をイベントに
@event.listens_for(User, 'after_insert')
def heavy_listener(mapper, connection, target):
    send_email(target)  # 遅い！
    call_external_api(target)  # 遅い！

# ✅ 非同期タスクキューに渡す
@event.listens_for(User, 'after_insert')
def light_listener(mapper, connection, target):
    queue.enqueue(send_email_task, target.id)
```

## まとめ

- **イベントシステム**: データベース操作の各段階でカスタムコード実行
- **ORMイベント**: before/after insert/update/delete
- **Flushイベント**: セッションの同期タイミング
- **コネクションイベント**: クエリロギング、初期化
- **監査ログ**: イベントで変更履歴を記録
- イベント内では重い処理を避ける

次の章では、継承とポリモーフィズムについて学びます。
