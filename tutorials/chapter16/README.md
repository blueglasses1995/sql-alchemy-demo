# 第16章: バッチ操作とパフォーマンス最適化

大量データの処理とパフォーマンス最適化のテクニックを学びます。

## Bulk Operations

### bulk_insert_mappings

```python
# 大量挿入（最速）
users_data = [
    {"name": f"User{i}", "email": f"user{i}@example.com"}
    for i in range(10000)
]

with Session(engine) as session:
    session.bulk_insert_mappings(User, users_data)
    session.commit()

# 特徴:
# ✅ 非常に高速
# ❌ リレーションシップ無視
# ❌ イベント発火しない
# ❌ バリデーションなし
```

### bulk_update_mappings

```python
# 大量更新
updates = [
    {"id": 1, "name": "Updated1"},
    {"id": 2, "name": "Updated2"},
    # ...
]

with Session(engine) as session:
    session.bulk_update_mappings(User, updates)
    session.commit()
```

## バッチ処理

### チャンク処理

```python
from sqlalchemy import select

BATCH_SIZE = 1000

with Session(engine) as session:
    offset = 0
    while True:
        # LIMIT/OFFSETで分割取得
        stmt = select(User).limit(BATCH_SIZE).offset(offset)
        users = session.execute(stmt).scalars().all()

        if not users:
            break

        # 処理
        for user in users:
            process_user(user)

        offset += BATCH_SIZE
        session.commit()  # バッチごとにコミット
```

### yield_per()

```python
# サーバーサイドカーソル（メモリ効率的）
with Session(engine) as session:
    stmt = select(User)

    for user in session.scalars(stmt).yield_per(1000):
        process_user(user)
        # 1000件ずつフェッチ
```

## Connection Pooling最適化

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://...',

    # プールサイズ
    pool_size=20,  # 常時保持する接続数

    # 最大オーバーフロー
    max_overflow=10,  # 一時的に追加できる接続数

    # 接続のタイムアウト
    pool_timeout=30,  # 接続取得までの待機時間(秒)

    # 接続の再利用制限
    pool_recycle=3600,  # 1時間で接続を再生成

    # 接続前のpingチェック
    pool_pre_ping=True,  # 接続が有効か確認
)
```

## Eager Loadingの最適化

```python
from sqlalchemy.orm import joinedload, selectinload, subqueryload

# ✅ selectinload（推奨）
stmt = select(User).options(
    selectinload(User.posts).selectinload(Post.comments)
)
# 3クエリ: users, posts, comments

# joinedload（1クエリだが重複あり）
stmt = select(User).options(
    joinedload(User.posts).joinedload(Post.comments)
)

# subqueryload
stmt = select(User).options(
    subqueryload(User.posts)
)
```

## インデックスの活用

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    # 単一カラムインデックス
    email: Mapped[str] = mapped_column(String(100), index=True)

    # 複合インデックス
    last_name: Mapped[str]
    first_name: Mapped[str]

    __table_args__ = (
        Index('ix_name', 'last_name', 'first_name'),
    )
```

## クエリ最適化

### 必要なカラムだけ取得

```python
# ❌ 全カラム取得
users = session.query(User).all()

# ✅ 必要なカラムだけ
stmt = select(User.id, User.name)
results = session.execute(stmt).all()
```

### EXISTS vs COUNT

```python
from sqlalchemy import exists

# ❌ 遅い
count = session.query(User).filter(User.is_active == True).count()
if count > 0:
    # ...

# ✅ 速い
stmt = exists().where(User.is_active == True)
has_users = session.query(stmt).scalar()
if has_users:
    # ...
```

## トランザクション最適化

```python
# ❌ トランザクションが多すぎる
for user in users:
    with session.begin():
        process(user)

# ✅ バッチでコミット
with session.begin():
    for i, user in enumerate(users):
        process(user)
        if i % 1000 == 0:
            session.flush()  # 中間フラッシュ
```

## まとめ

- `bulk_insert_mappings`: 最速の挿入
- `yield_per()`: メモリ効率的な取得
- Connection Pooling: 適切なサイズ設定
- Eager Loading: N+1問題を回避
- インデックス: 検索を高速化
- クエリ最適化: 必要なデータだけ取得
