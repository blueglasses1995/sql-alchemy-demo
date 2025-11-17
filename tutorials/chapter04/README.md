# 第4章: CRUD操作とセッション管理

## 学習目標
- Sessionの役割と重要性を理解する
- Create（作成）、Read（読み取り）、Update（更新）、Delete（削除）の実装方法を学ぶ
- トランザクション管理を理解する
- セッションのライフサイクルを把握する

## Sessionとは

**Session**は、ORMにおける「作業単位（Unit of Work）」を管理するオブジェクトです。

### Sessionの役割

```
┌─────────────────────────────────────┐
│         Session                     │
│  ┌───────────────────────────────┐  │
│  │  Identity Map                 │  │
│  │  User:1 → <User id=1>         │  │
│  │  User:2 → <User id=2>         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Unit of Work                 │  │
│  │  New:      [user3]            │  │
│  │  Modified: [user1]            │  │
│  │  Deleted:  [user2]            │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Transaction                  │  │
│  │  BEGIN → ... → COMMIT/ROLLBACK│  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

1. **Identity Map**: オブジェクトの一意性を保証
2. **Unit of Work**: 変更の追跡と一括コミット
3. **Transaction**: トランザクション管理

### Sessionの作成

```python
from sqlalchemy.orm import Session, sessionmaker

# 方法1: Sessionクラスを直接使用
session = Session(engine)

# 方法2: sessionmakerを使用（推奨）
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 方法3: コンテキストマネージャー
with Session(engine) as session:
    # 作業
    session.commit()
```

## Create（作成）

### 基本的な作成

```python
from sqlalchemy.orm import Session

# 新しいユーザーを作成
new_user = User(
    username="alice",
    email="alice@example.com",
    full_name="Alice Smith"
)

with Session(engine) as session:
    # セッションに追加
    session.add(new_user)

    # データベースに保存
    session.commit()

    # IDが自動的に割り当てられる
    print(f"作成されたユーザーID: {new_user.id}")
```

### 内部動作

```
1. user = User(...)
   ├─ Pythonオブジェクト作成
   └─ まだDBには保存されていない

2. session.add(user)
   ├─ Sessionの"new"リストに追加
   └─ まだSQLは実行されない

3. session.commit()
   ├─ BEGIN TRANSACTION
   ├─ INSERT INTO users (...) VALUES (...)
   ├─ COMMIT
   └─ user.id が自動的にセットされる
```

### 複数のオブジェクトを一括作成

```python
users = [
    User(username="bob", email="bob@example.com"),
    User(username="charlie", email="charlie@example.com"),
    User(username="dave", email="dave@example.com"),
]

with Session(engine) as session:
    # add_all()で一括追加
    session.add_all(users)
    session.commit()
```

## Read（読み取り）

### 主キーで取得

```python
with Session(engine) as session:
    # get()で主キーから取得
    user = session.get(User, 1)  # ID=1のユーザー

    if user:
        print(f"見つかりました: {user.username}")
    else:
        print("ユーザーが見つかりません")
```

### 全件取得

```python
from sqlalchemy import select

with Session(engine) as session:
    # select文を構築
    stmt = select(User)

    # 実行して全件取得
    users = session.execute(stmt).scalars().all()

    for user in users:
        print(f"{user.id}: {user.username}")
```

### 条件付き検索

```python
with Session(engine) as session:
    # WHERE句
    stmt = select(User).where(User.username == "alice")
    user = session.execute(stmt).scalar_one_or_none()

    # 複数条件（AND）
    stmt = select(User).where(
        User.is_active == True,
        User.username.like("a%")
    )

    # OR条件
    from sqlalchemy import or_
    stmt = select(User).where(
        or_(
            User.username == "alice",
            User.username == "bob"
        )
    )
```

### クエリメソッド

```python
from sqlalchemy import select

with Session(engine) as session:
    # 1件取得（必ず存在する前提）
    user = session.execute(
        select(User).where(User.id == 1)
    ).scalar_one()

    # 1件または0件
    user = session.execute(
        select(User).where(User.username == "alice")
    ).scalar_one_or_none()

    # 最初の1件
    user = session.execute(
        select(User)
    ).scalar()

    # 全件
    users = session.execute(select(User)).scalars().all()
```

### ソートと制限

```python
with Session(engine) as session:
    # ORDER BY
    stmt = select(User).order_by(User.created_at.desc())

    # LIMIT
    stmt = select(User).limit(10)

    # OFFSET（ページネーション）
    stmt = select(User).limit(10).offset(20)

    users = session.execute(stmt).scalars().all()
```

## Update（更新）

### オブジェクトの属性を変更

```python
with Session(engine) as session:
    # ユーザーを取得
    user = session.get(User, 1)

    # 属性を変更
    user.email = "newemail@example.com"
    user.full_name = "Alice Johnson"

    # コミット（自動的にUPDATE文が発行される）
    session.commit()
```

**内部動作**:

```
1. user = session.get(User, 1)
   └─ SELECT * FROM users WHERE id = 1

2. user.email = "newemail@example.com"
   ├─ Sessionが変更を検知
   └─ "modified"リストに追加

3. session.commit()
   ├─ BEGIN TRANSACTION
   ├─ UPDATE users SET email = 'newemail@...'
   │  WHERE id = 1
   └─ COMMIT
```

### 一括更新

```python
from sqlalchemy import update

with Session(engine) as session:
    # UPDATE文を直接実行
    stmt = update(User).where(
        User.is_active == False
    ).values(
        is_active=True
    )

    session.execute(stmt)
    session.commit()
```

## Delete（削除）

### オブジェクトを削除

```python
with Session(engine) as session:
    # ユーザーを取得
    user = session.get(User, 1)

    # 削除
    session.delete(user)

    # コミット
    session.commit()
```

### 一括削除

```python
from sqlalchemy import delete

with Session(engine) as session:
    # DELETE文を直接実行
    stmt = delete(User).where(User.is_active == False)

    result = session.execute(stmt)
    session.commit()

    print(f"{result.rowcount}件削除しました")
```

## トランザクション管理

### 自動コミット

```python
# コンテキストマネージャーで自動コミット
with Session(engine) as session:
    user = User(username="alice")
    session.add(user)
    # ブロックを抜ける時に自動的にcommit()
```

### 明示的なロールバック

```python
with Session(engine) as session:
    try:
        user = User(username="alice")
        session.add(user)

        # エラーが発生する可能性がある処理
        # ...

        session.commit()
    except Exception as e:
        session.rollback()  # エラー時はロールバック
        print(f"エラーが発生しました: {e}")
        raise
```

### ネストしたトランザクション

```python
with Session(engine) as session:
    user1 = User(username="alice")
    session.add(user1)

    # セーブポイント
    with session.begin_nested():
        user2 = User(username="bob")
        session.add(user2)
        # エラーが発生してもuser1は保存される

    session.commit()
```

## セッションのライフサイクル

### セッションの状態

```
┌──────────────┐
│ Transient    │  新規作成、セッションと無関係
│（一時的）     │  user = User(...)
└──────┬───────┘
       │ session.add()
       ▼
┌──────────────┐
│ Pending      │  セッションに追加済み、未保存
│（保留中）     │  INSERT予定
└──────┬───────┘
       │ session.commit()
       ▼
┌──────────────┐
│ Persistent   │  DBに保存済み、セッションで管理中
│（永続的）     │  変更を追跡
└──────┬───────┘
       │ session.delete()
       ▼
┌──────────────┐
│ Deleted      │  削除予定
│（削除済み）   │  DELETE予定
└──────┬───────┘
       │ session.commit()
       ▼
┌──────────────┐
│ Detached     │  セッションから切り離された
│（分離）       │  session.close()後
└──────────────┘
```

### オブジェクト状態の確認

```python
from sqlalchemy import inspect

user = User(username="alice")
print(inspect(user).transient)  # True

session.add(user)
print(inspect(user).pending)    # True

session.commit()
print(inspect(user).persistent) # True

session.delete(user)
print(inspect(user).deleted)    # True
```

## 実践ハンズオン

`01_crud_basic.py`を作成:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, User  # 第3章で作成したモデル

engine = create_engine('sqlite:///tutorial.db')

# --- CREATE ---
print("=== CREATE ===")
with Session(engine) as session:
    new_user = User(
        username="alice",
        email="alice@example.com",
        full_name="Alice Smith"
    )
    session.add(new_user)
    session.commit()
    print(f"作成: {new_user}")

# --- READ ---
print("\n=== READ ===")
with Session(engine) as session:
    # 全件取得
    users = session.execute(select(User)).scalars().all()
    for user in users:
        print(f"  {user}")

# --- UPDATE ---
print("\n=== UPDATE ===")
with Session(engine) as session:
    user = session.get(User, 1)
    user.email = "alice_updated@example.com"
    session.commit()
    print(f"更新: {user}")

# --- DELETE ---
print("\n=== DELETE ===")
with Session(engine) as session:
    user = session.get(User, 1)
    session.delete(user)
    session.commit()
    print("削除完了")
```

## まとめ

- **Session**はUnit of Workパターンでデータ操作を管理
- **Create**: `add()`でオブジェクトを追加
- **Read**: `select()`でクエリ構築、`execute()`で実行
- **Update**: 属性変更後`commit()`で自動UPDATE
- **Delete**: `delete()`で削除をマーク
- `commit()`で変更をDBに反映、`rollback()`で取り消し

次の章では、テーブル間のリレーションシップについて学びます。
