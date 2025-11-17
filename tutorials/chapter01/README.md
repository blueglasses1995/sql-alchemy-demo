# 第1章: SQLAlchemy入門

## 学習目標
- SQLAlchemyとは何かを理解する
- ORMとCore APIの違いを理解する
- SQLAlchemyのアーキテクチャを把握する

## SQLAlchemyとは

SQLAlchemyは、Pythonで最も人気のあるSQL toolkit/ORMです。2006年にMike Bayerによって開発され、現在も活発にメンテナンスされています。

### 主な特徴

1. **柔軟性**: 生SQL、SQL Expression Language、ORMの3つのレベルで利用可能
2. **データベース非依存**: SQLite、PostgreSQL、MySQL、Oracle等に対応
3. **強力**: エンタープライズレベルのアプリケーションに対応
4. **Pythonic**: Pythonらしい直感的なAPI

## SQLAlchemyのアーキテクチャ

SQLAlchemyは大きく2つの層から構成されています：

```
┌─────────────────────────────────────────┐
│         アプリケーション                │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│   ORM Layer    │    │   Core Layer    │
│                │    │                 │
│  - Session     │    │  - Engine       │
│  - Query       │    │  - Connection   │
│  - Mapper      │    │  - SQL Expr     │
└───────┬────────┘    └────────┬────────┘
        │                       │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │     DBAPI (PEP 249)   │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │   データベース        │
        │ (SQLite/PostgreSQL)  │
        └───────────────────────┘
```

### 1. Core Layer（コア層）

**役割**: データベースとの低レベルな対話を担当

**主要コンポーネント**:
- **Engine**: データベース接続を管理
- **Connection**: 実際のDB接続を表現
- **SQL Expression Language**: SQLをPythonオブジェクトで表現

**特徴**:
- より細かい制御が可能
- パフォーマンスに優れる
- SQL文を直接操作する感覚に近い

```python
# Core APIの例
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String)
)

# SQL Expression
select_stmt = users.select().where(users.c.name == 'Alice')
```

### 2. ORM Layer（ORM層）

**役割**: Pythonオブジェクトとデータベーステーブルをマッピング

**主要コンポーネント**:
- **Session**: 作業単位（Unit of Work）を管理
- **Mapper**: クラスとテーブルの対応関係を定義
- **Query**: オブジェクト指向的なクエリAPI

**特徴**:
- オブジェクト指向的に扱える
- リレーションシップの管理が容易
- 開発効率が高い

```python
# ORM APIの例
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

# オブジェクト指向的な操作
user = User(name='Alice')
session.add(user)
```

## Core vs ORM: どちらを使うべきか？

### Core APIを使うべき場合

✅ 大量データの一括処理
✅ 複雑なSQL文が必要
✅ パフォーマンスが最重要
✅ 既存のデータベーススキーマに対応

### ORM APIを使うべき場合

✅ CRUDが中心のアプリケーション
✅ オブジェクト指向的な設計
✅ リレーションシップの管理が重要
✅ 開発速度を優先

### ハイブリッドアプローチ

実際のアプリケーションでは、両方を組み合わせて使用することが多いです：

- 通常の操作はORM
- 複雑なレポートや集計はCore
- 一括更新/削除はCore

## SQLAlchemyの内部動作原理

### 1. Identity Map（アイデンティティマップ）

ORMは「Identity Map」パターンを使用して、同じデータベースレコードに対して常に同じPythonオブジェクトを返します。

```
Session (アイデンティティマップ)
┌─────────────────────────────────┐
│  Key      │  Object              │
│──────────────────────────────────│
│ User:1    │  <User id=1>         │
│ User:2    │  <User id=2>         │
│ Post:1    │  <Post id=1>         │
└─────────────────────────────────┘

# 同じIDのユーザーを2回取得しても、同一オブジェクト
user1 = session.get(User, 1)
user2 = session.get(User, 1)
assert user1 is user2  # True!
```

**メリット**:
- メモリ効率
- データの一貫性保証
- パフォーマンス向上（キャッシュ効果）

### 2. Unit of Work（作業単位）

ORMは「Unit of Work」パターンで変更を追跡し、コミット時にまとめてデータベースに反映します。

```
                Unit of Work
    ┌──────────────────────────────────┐
    │  New Objects:    [user1, post1]  │
    │  Modified:       [user2]         │
    │  Deleted:        [post2]         │
    └──────────────────────────────────┘
                        │
              session.commit()
                        │
                        ▼
    ┌──────────────────────────────────┐
    │  INSERT INTO users ...           │
    │  INSERT INTO posts ...           │
    │  UPDATE users SET ...            │
    │  DELETE FROM posts ...           │
    │  COMMIT;                         │
    └──────────────────────────────────┘
```

**メリット**:
- トランザクション管理が容易
- 最適化されたSQL実行
- データ整合性の保証

### 3. Lazy Loading（遅延読み込み）

関連オブジェクトは、実際にアクセスされるまでデータベースから読み込まれません。

```python
# UserとPostが1対多の関係の場合

user = session.get(User, 1)
# この時点ではSELECT * FROM users WHERE id=1だけ実行

print(user.posts)  # ← ここで初めてpostsを読み込む
# SELECT * FROM posts WHERE user_id=1が実行される
```

**注意点（N+1問題）**:

```python
# ❌ 悪い例: N+1クエリが発生
users = session.query(User).all()  # 1クエリ
for user in users:
    print(user.posts)  # Nクエリ（ユーザー数分）

# ✅ 良い例: Eager Loading
from sqlalchemy.orm import joinedload

users = session.query(User).options(
    joinedload(User.posts)
).all()  # 1クエリでJOINして取得
```

## まとめ

- SQLAlchemyはCore（低レベル）とORM（高レベル）の2層構造
- ORMはIdentity Map、Unit of Work、Lazy Loadingなどのパターンを実装
- 用途に応じてCoreとORMを使い分ける
- 両方を組み合わせることで最大の効果を発揮

次の章では、実際にデータベースに接続してみましょう。
