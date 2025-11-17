# 第6章: 高度なクエリとSQLAlchemy Core

## 学習目標
- 複雑なクエリの構築方法を学ぶ
- 集約関数とグループ化を理解する
- サブクエリの使い方を習得する
- Core APIを活用する

## 高度なフィルタリング

### 複数条件の組み合わせ

```python
from sqlalchemy import select, and_, or_, not_

# AND条件
stmt = select(User).where(
    and_(
        User.is_active == True,
        User.age >= 18
    )
)

# OR条件
stmt = select(User).where(
    or_(
        User.name == "Alice",
        User.name == "Bob"
    )
)

# NOT条件
stmt = select(User).where(
    not_(User.is_active == True)
)

# 組み合わせ
stmt = select(User).where(
    and_(
        User.is_active == True,
        or_(
            User.age >= 18,
            User.parental_consent == True
        )
    )
)
```

### パターンマッチング

```python
# LIKE
stmt = select(User).where(User.name.like("A%"))  # Aで始まる

# ILIKE（大文字小文字を区別しない）
stmt = select(User).where(User.name.ilike("alice"))

# IN
stmt = select(User).where(User.id.in_([1, 2, 3]))

# BETWEEN
stmt = select(User).where(User.age.between(18, 30))

# IS NULL
stmt = select(User).where(User.deleted_at.is_(None))

# IS NOT NULL
stmt = select(User).where(User.deleted_at.isnot(None))
```

## 集約とグループ化

### COUNT, SUM, AVG, MAX, MIN

```python
from sqlalchemy import func, select

# COUNT
stmt = select(func.count(User.id))
count = session.execute(stmt).scalar()

# AVG
stmt = select(func.avg(User.age))
avg_age = session.execute(stmt).scalar()

# MAX/MIN
stmt = select(func.max(User.created_at))
latest = session.execute(stmt).scalar()

# SUM
stmt = select(func.sum(Product.price))
total = session.execute(stmt).scalar()
```

### GROUP BY

```python
# ユーザーごとの投稿数
stmt = select(
    User.name,
    func.count(Post.id).label('post_count')
).join(Post).group_by(User.id)

results = session.execute(stmt).all()
for name, count in results:
    print(f"{name}: {count}件")
```

### HAVING

```python
# 投稿が3件以上のユーザー
stmt = select(
    User.name,
    func.count(Post.id).label('post_count')
).join(Post).group_by(User.id).having(
    func.count(Post.id) >= 3
)
```

### 集約の仕組み

```
元データ（posts）
┌────┬───────┬─────────┐
│ id │ title │ user_id │
├────┼───────┼─────────┤
│ 1  │ Post1 │ 1       │
│ 2  │ Post2 │ 1       │
│ 3  │ Post3 │ 2       │
│ 4  │ Post4 │ 1       │
└────┴───────┴─────────┘

GROUP BY user_id
↓
┌─────────┬──────────┐
│ user_id │ count(*) │
├─────────┼──────────┤
│ 1       │ 3        │
│ 2       │ 1        │
└─────────┴──────────┘
```

## JOIN

### 内部結合（INNER JOIN）

```python
# 投稿を持つユーザーのみ
stmt = select(User).join(Post)

# 明示的な条件指定
stmt = select(User).join(Post, User.id == Post.user_id)
```

### 外部結合（OUTER JOIN）

```python
# 投稿がないユーザーも含める
stmt = select(User).outerjoin(Post)

# 左外部結合（LEFT OUTER JOIN）
stmt = select(User).join(Post, isouter=True)
```

### JOINの図解

```
INNER JOIN
users           posts
┌────┬─────┐   ┌────┬─────────┐
│ 1  │Alice│──┐│ 1  │ user_id:1│ ✓
│ 2  │Bob  │  └│ 2  │ user_id:1│ ✓
│ 3  │Carol│   │ 3  │ user_id:2│ ✓
└────┴─────┘   └────┴─────────┘

結果: Alice, Bob (投稿がある人のみ)

LEFT OUTER JOIN
users           posts
┌────┬─────┐   ┌────┬─────────┐
│ 1  │Alice│──┐│ 1  │ user_id:1│ ✓
│ 2  │Bob  │  └│ 2  │ user_id:1│ ✓
│ 3  │Carol│   │ 3  │ user_id:2│ ✓
└────┴─────┘   └────┴─────────┘

結果: Alice, Bob, Carol (全ユーザー)
```

## サブクエリ

### スカラーサブクエリ

```python
# 各ユーザーの投稿数を含めて取得
post_count = (
    select(func.count(Post.id))
    .where(Post.user_id == User.id)
    .scalar_subquery()
)

stmt = select(User.name, post_count.label('post_count'))
results = session.execute(stmt).all()
```

### EXISTS

```python
# 投稿を持つユーザーのみ
has_posts = select(1).where(Post.user_id == User.id).exists()

stmt = select(User).where(has_posts)
```

### IN with subquery

```python
# 最新の投稿を持つユーザー
latest_post_ids = select(Post.id).order_by(
    Post.created_at.desc()
).limit(10)

stmt = select(User).where(
    User.id.in_(
        select(Post.user_id).where(Post.id.in_(latest_post_ids))
    )
)
```

## SQLAlchemy Core API

### Coreとは

ORMを使わず、SQLをPythonオブジェクトで表現する低レベルAPI

```
ORM (高レベル)
    ↓
  Core (低レベル)
    ↓
  DBAPI
    ↓
データベース
```

### Tableオブジェクト

```python
from sqlalchemy import Table, Column, Integer, String, MetaData

metadata = MetaData()

users_table = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('email', String(100))
)
```

### Core APIでのCRUD

```python
from sqlalchemy import insert, select, update, delete

# INSERT
stmt = insert(users_table).values(
    name="Alice",
    email="alice@example.com"
)
result = conn.execute(stmt)

# SELECT
stmt = select(users_table).where(users_table.c.name == "Alice")
result = conn.execute(stmt)
for row in result:
    print(row.name, row.email)

# UPDATE
stmt = update(users_table).where(
    users_table.c.id == 1
).values(email="newemail@example.com")
conn.execute(stmt)

# DELETE
stmt = delete(users_table).where(users_table.c.id == 1)
conn.execute(stmt)
```

### Core vs ORM

```
Core API
✅ 高速（オーバーヘッドが少ない）
✅ 柔軟（複雑なSQLを直接書ける）
✅ 一括処理に向いている
❌ オブジェクトとして扱えない
❌ リレーションシップの管理が手動

ORM API
✅ オブジェクト指向的
✅ リレーションシップ管理が容易
✅ 開発効率が高い
❌ 若干のオーバーヘッド
❌ 複雑なクエリは記述が冗長
```

## ウィンドウ関数

### ROW_NUMBER

```python
from sqlalchemy import over

# ユーザーごとに投稿を番号付け
stmt = select(
    Post.title,
    Post.user_id,
    func.row_number().over(
        partition_by=Post.user_id,
        order_by=Post.created_at.desc()
    ).label('row_num')
)
```

### RANK, DENSE_RANK

```python
# スコアのランキング
stmt = select(
    User.name,
    User.score,
    func.rank().over(order_by=User.score.desc()).label('rank')
)
```

## 実践ハンズオン

`01_advanced_queries.py`を作成:

```python
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from models import User, Post

engine = create_engine('sqlite:///tutorial.db')

with Session(engine) as session:
    # 集約: ユーザーごとの投稿数
    stmt = select(
        User.name,
        func.count(Post.id).label('post_count')
    ).join(Post).group_by(User.id)

    print("=== ユーザーごとの投稿数 ===")
    for name, count in session.execute(stmt):
        print(f"{name}: {count}件")

    # サブクエリ: 平均より多く投稿しているユーザー
    avg_posts = select(
        func.count(Post.id)
    ).group_by(Post.user_id).scalar_subquery()

    stmt = select(User).where(
        select(func.count(Post.id))
        .where(Post.user_id == User.id)
        .scalar_subquery() > func.avg(avg_posts)
    )

    print("\n=== 平均より多く投稿しているユーザー ===")
    for user in session.execute(stmt).scalars():
        print(user.name)
```

## まとめ

- 複雑な条件は`and_()`, `or_()`, `not_()`で組み合わせ
- 集約関数で統計情報を取得
- `GROUP BY`と`HAVING`でグループ化と絞り込み
- サブクエリで高度な検索が可能
- Core APIは高速だがORMほど便利ではない

次の章では、Alembicを使ったマイグレーション管理を学びます。
