# 第8章: 非同期SQLAlchemy (AsyncIO)

## 学習目標
- SQLAlchemy 2.0の非同期サポートを理解する
- AsyncEngineとAsyncSessionの使い方を学ぶ
- async/awaitパターンでのデータベース操作を習得する
- 非同期処理のベストプラクティスを理解する

## 非同期SQLAlchemyとは

SQLAlchemy 2.0では、Pythonの`asyncio`を完全サポートし、非同期I/Oによる高速なデータベース操作が可能です。

### 同期 vs 非同期

```
同期処理（従来）
┌──────────┐
│ Thread 1 │  DB接続 ───→ 待機 ───→ 結果受信
└──────────┘           (ブロック)

非同期処理（AsyncIO）
┌──────────┐
│ Task 1   │  DB接続 ───→ 他の処理 ─→ 結果受信
│ Task 2   │    └─────→ DB接続 ───→ 結果受信
│ Task 3   │              └───→ DB接続 ─→ 結果
└──────────┘
  同時実行（並行処理）
```

### メリット

- **高いスループット**: I/O待機中に他の処理を実行
- **リソース効率**: スレッドより軽量
- **スケーラビリティ**: 多数の同時接続に対応

## AsyncEngineの作成

### 基本的な使い方

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# 非同期エンジンの作成
# 注: URLに "postgresql+asyncpg" または "sqlite+aiosqlite" を使用
engine = create_async_engine(
    "sqlite+aiosqlite:///async_tutorial.db",
    echo=True
)

# 非同期セッションファクトリ
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

### 対応ドライバ

```
PostgreSQL
  └─ asyncpg (推奨)
     sqlalchemy.url = postgresql+asyncpg://user:pass@host/db

MySQL
  └─ aiomysql
     sqlalchemy.url = mysql+aiomysql://user:pass@host/db

SQLite
  └─ aiosqlite
     sqlalchemy.url = sqlite+aiosqlite:///file.db
```

## 非同期モデル定義

モデル定義自体は同期版と同じです。

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"
```

## 非同期CRUD操作

### テーブル作成

```python
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**重要**: `create_all()`は同期メソッドなので、`run_sync()`でラップします。

### Create（作成）

```python
async def create_user(name: str, email: str):
    async with async_session() as session:
        new_user = User(name=name, email=email)
        session.add(new_user)
        await session.commit()
        return new_user

# 使用例
import asyncio

async def main():
    user = await create_user("Alice", "alice@example.com")
    print(f"作成: {user}")

asyncio.run(main())
```

### Read（読み取り）

```python
from sqlalchemy import select

async def get_user(user_id: int):
    async with async_session() as session:
        # get()を使う場合
        user = await session.get(User, user_id)
        return user

async def get_users():
    async with async_session() as session:
        # select()を使う場合
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        return users

async def search_users(name_pattern: str):
    async with async_session() as session:
        stmt = select(User).where(User.name.like(f"%{name_pattern}%"))
        result = await session.execute(stmt)
        users = result.scalars().all()
        return users
```

### Update（更新）

```python
async def update_user(user_id: int, new_email: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.email = new_email
            await session.commit()
        return user
```

### Delete（削除）

```python
async def delete_user(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()
```

## 非同期リレーションシップ

### モデル定義

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import List

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    posts: Mapped[List["Post"]] = relationship(back_populates="user")

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
```

### Eager Loading

```python
from sqlalchemy.orm import selectinload

async def get_users_with_posts():
    async with async_session() as session:
        # selectinloadで事前読み込み
        stmt = select(User).options(selectinload(User.posts))
        result = await session.execute(stmt)
        users = result.scalars().all()

        for user in users:
            print(f"{user.name}の投稿:")
            for post in user.posts:
                print(f"  - {post.title}")
```

**注意**: Lazy Loadingは非同期では使えません。必ずEager Loadingを使用してください。

```python
# ❌ これはエラーになる
async with async_session() as session:
    user = await session.get(User, 1)
    # セッションの外でアクセスするとエラー
    print(user.posts)  # DetachedInstanceError

# ✅ 正しい方法
async with async_session() as session:
    stmt = select(User).options(selectinload(User.posts)).where(User.id == 1)
    result = await session.execute(stmt)
    user = result.scalar_one()
    print(user.posts)  # OK
```

## 並行処理

### 複数のクエリを同時実行

```python
import asyncio

async def parallel_queries():
    # 複数のタスクを同時実行
    users_task = get_users()
    user_1_task = get_user(1)
    search_task = search_users("Alice")

    # 全てのタスクの完了を待つ
    users, user_1, search_results = await asyncio.gather(
        users_task,
        user_1_task,
        search_task
    )

    print(f"全ユーザー: {len(users)}人")
    print(f"ユーザー1: {user_1}")
    print(f"検索結果: {len(search_results)}人")
```

### 大量の挿入を並行処理

```python
async def bulk_create_users(count: int):
    tasks = []
    for i in range(count):
        task = create_user(f"User{i}", f"user{i}@example.com")
        tasks.append(task)

    # 全ての挿入を並行実行
    users = await asyncio.gather(*tasks)
    print(f"{len(users)}人のユーザーを作成しました")
```

## トランザクション管理

### 明示的なトランザクション

```python
async def transfer_data():
    async with async_session() as session:
        async with session.begin():
            # トランザクション内での処理
            user1 = await session.get(User, 1)
            user2 = await session.get(User, 2)

            # 何か処理...

            # 自動的にコミットされる
```

### ロールバック

```python
async def risky_operation():
    async with async_session() as session:
        try:
            async with session.begin():
                user = User(name="Test", email="test@example.com")
                session.add(user)

                # エラーが発生する可能性のある処理
                raise Exception("Something went wrong")

        except Exception as e:
            # 自動的にロールバックされる
            print(f"エラー: {e}")
```

## 実践ハンズオン

### 完全な例

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Base, User, Post  # 既存のモデル

# エンジン作成
engine = create_async_engine(
    "sqlite+aiosqlite:///async_tutorial.db",
    echo=True
)

# セッションファクトリ
async_session = async_sessionmaker(engine, class_=AsyncSession)

async def init_db():
    """テーブル作成"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # テーブル作成
    await init_db()

    # ユーザー作成
    async with async_session() as session:
        users = [
            User(name="Alice", email="alice@example.com"),
            User(name="Bob", email="bob@example.com"),
        ]
        session.add_all(users)
        await session.commit()

    # 読み取り
    async with async_session() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        all_users = result.scalars().all()

        print("=== 全ユーザー ===")
        for user in all_users:
            print(f"  {user}")

    # エンジンのクリーンアップ
    await engine.dispose()

# 実行
if __name__ == "__main__":
    asyncio.run(main())
```

## パフォーマンス比較

### 同期版

```python
import time

def sync_operations():
    start = time.time()

    for i in range(100):
        user = session.get(User, i)  # 各クエリでブロック

    print(f"同期: {time.time() - start:.2f}秒")
```

### 非同期版

```python
async def async_operations():
    start = time.time()

    tasks = [session.get(User, i) for i in range(100)]
    await asyncio.gather(*tasks)  # 並行実行

    print(f"非同期: {time.time() - start:.2f}秒")
```

**結果**: 非同期版は通常2-10倍高速

## ベストプラクティス

### 1. セッションのライフサイクル

```python
# ✅ 良い例: コンテキストマネージャーを使用
async with async_session() as session:
    # 処理
    await session.commit()

# ❌ 悪い例: セッションを閉じ忘れ
session = async_session()
# ...
```

### 2. 必ずEager Loadingを使用

```python
# ✅ 良い例
stmt = select(User).options(selectinload(User.posts))

# ❌ 悪い例: Lazy Loadingは非同期で動作しない
user = await session.get(User, 1)
posts = user.posts  # エラー！
```

### 3. エンジンの使い回し

```python
# ✅ 良い例: アプリケーション全体で1つのエンジン
engine = create_async_engine(...)

# ❌ 悪い例: リクエストごとにエンジン作成
async def handler():
    engine = create_async_engine(...)  # NG!
```

## まとめ

- SQLAlchemy 2.0は`asyncio`を完全サポート
- `create_async_engine`と`AsyncSession`を使用
- **Lazy Loadingは使えない** → Eager Loadingを使用
- `asyncio.gather()`で並行処理が可能
- 同期版より2-10倍高速化できる

次の章では、Hybrid PropertiesとExpressionについて学びます。
