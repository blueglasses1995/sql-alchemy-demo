# 第3章: モデル定義とテーブルマッピング

## 学習目標
- ORMモデルの定義方法を理解する
- Mapped型とmapped_columnの使い方を学ぶ
- カラムの型とオプションを理解する
- テーブル作成の仕組みを学ぶ

## ORMモデルとは

ORMモデルは、Pythonのクラスとデータベースのテーブルを対応付ける仕組みです。

```
Python側                      データベース側
┌──────────────┐              ┌──────────────┐
│  class User  │    ←→        │  users table │
├──────────────┤    マッピング ├──────────────┤
│ id: int      │    ←→        │ id INTEGER   │
│ name: str    │    ←→        │ name VARCHAR │
│ email: str   │    ←→        │ email VARCHAR│
└──────────────┘              └──────────────┘

user = User(                  INSERT INTO users
    name="Alice",             (name, email)
    email="alice@..."         VALUES
)                             ('Alice', 'alice@...')
```

## DeclarativeBaseによるモデル定義

SQLAlchemy 2.0では`DeclarativeBase`を使用します。

### 基本的なモデル

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ベースクラスの定義（アプリ全体で1つ）
class Base(DeclarativeBase):
    pass

# Userモデルの定義
class User(Base):
    __tablename__ = 'users'  # テーブル名

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
```

### モデル定義の構成要素

```
class User(Base):
      ↑     ↑
      │     └─ 全モデルの基底クラス
      └─────── モデルクラス名（通常は単数形）

    __tablename__ = 'users'
                     ↑
                     └─ データベースのテーブル名（通常は複数形）

    id: Mapped[int] = mapped_column(primary_key=True)
    ↑   ↑      ↑     ↑              ↑
    │   │      │     │              └─ カラムのオプション
    │   │      │     └──────────────── カラム定義
    │   │      └────────────────────── Python型
    │   └───────────────────────────── Mapped型（必須）
    └───────────────────────────────── 属性名（=カラム名）
```

## Mapped型の理解

`Mapped[T]`は、SQLAlchemyのORM属性であることを示す型ヒントです。

### Mapped型の役割

```python
# ❌ 古い書き方（SQLAlchemy 1.x）
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)  # 型ヒントなし
    name = Column(String)                    # 型が不明瞭

# ✅ 新しい書き方（SQLAlchemy 2.0+）
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
```

**メリット**:
- IDE/エディタの型チェックが効く
- 自動補完が正確になる
- コードの可読性向上

### Nullableな値の表現

```python
from typing import Optional

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    # NOT NULL（必須）
    name: Mapped[str]

    # NULL許容（オプション）
    nickname: Mapped[Optional[str]]

    # デフォルト値あり（NULL許容）
    age: Mapped[Optional[int]] = mapped_column(default=0)
```

## カラムの型

SQLAlchemyは、Python型からSQL型への自動変換をサポートします。

### 基本的な型マッピング

```python
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal

class Product(Base):
    __tablename__ = 'products'

    # 整数
    id: Mapped[int]              # → INTEGER

    # 文字列
    name: Mapped[str]            # → VARCHAR

    # 浮動小数点
    weight: Mapped[float]        # → FLOAT

    # 真偽値
    is_active: Mapped[bool]      # → BOOLEAN (or INTEGER 0/1)

    # 日付・時刻
    created_at: Mapped[datetime] # → DATETIME
    birthday: Mapped[date]       # → DATE

    # 固定小数点（金額等）
    price: Mapped[Decimal]       # → NUMERIC/DECIMAL
```

### 明示的な型指定

```python
from sqlalchemy import String, Text, Integer

class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(primary_key=True)

    # 長さ指定
    title: Mapped[str] = mapped_column(String(200))

    # 長文
    content: Mapped[str] = mapped_column(Text)

    # 符号なし整数（データベース依存）
    view_count: Mapped[int] = mapped_column(Integer, unsigned=True)
```

### 型マッピングの詳細

```
Python型               SQL型（デフォルト）
─────────────────────  ──────────────────
int                    INTEGER
str                    VARCHAR
float                  FLOAT
bool                   BOOLEAN
datetime.datetime      DATETIME
datetime.date          DATE
datetime.time          TIME
decimal.Decimal        NUMERIC
bytes                  BLOB/BYTEA
dict/list (with JSON)  JSON
```

## カラムオプション

### 主要なオプション

```python
from sqlalchemy import String
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    # 主キー
    id: Mapped[int] = mapped_column(primary_key=True)

    # 一意制約
    email: Mapped[str] = mapped_column(unique=True)

    # NOT NULL（Mapped型で制御）
    name: Mapped[str]  # NOT NULL

    # NULL許容
    nickname: Mapped[Optional[str]]  # NULL OK

    # デフォルト値（Python側）
    is_active: Mapped[bool] = mapped_column(default=True)

    # デフォルト値（SQL側）- 関数
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    # サーバー側デフォルト（SQLの式）
    updated_at: Mapped[datetime] = mapped_column(
        server_default="CURRENT_TIMESTAMP"
    )

    # インデックス
    username: Mapped[str] = mapped_column(index=True)

    # カラム名の上書き
    full_name: Mapped[str] = mapped_column("name", String(100))
```

### オプションの組み合わせ

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    # ユニーク + インデックス + NOT NULL
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # デフォルト値 + サーバー側更新
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP"
    )

    # 自動更新（UPDATE時）
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_onupdate="CURRENT_TIMESTAMP"
    )
```

## テーブル作成の仕組み

### MetaDataとは

`DeclarativeBase`は内部的に`MetaData`オブジェクトを持ち、全テーブルの情報を管理します。

```
Base (DeclarativeBase)
  │
  ├─ metadata (MetaData)
  │   │
  │   ├─ Table('users', ...)
  │   ├─ Table('posts', ...)
  │   └─ Table('comments', ...)
  │
  ├─ User class
  ├─ Post class
  └─ Comment class
```

### create_all()でテーブル作成

```python
from sqlalchemy import create_engine

# エンジン作成
engine = create_engine('sqlite:///tutorial.db')

# すべてのテーブルを作成
Base.metadata.create_all(engine)
```

**内部動作**:

```
1. Baseに登録された全クラスをスキャン
   ↓
2. 各クラスの__tablename__とカラム定義を読み取る
   ↓
3. CREATE TABLE文を生成
   ↓
4. データベースに実行
   ↓
5. 既に存在するテーブルはスキップ
```

### 実際に生成されるSQL

```python
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default="CURRENT_TIMESTAMP"
    )
```

↓ SQLite

```sql
CREATE TABLE users (
    id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE (email)
);
```

## 実践ハンズオン

### 1. 基本的なモデル定義

`01_basic_model.py`を作成:

```python
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from typing import Optional

# ベースクラス
class Base(DeclarativeBase):
    pass

# Userモデル
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# エンジン作成
engine = create_engine('sqlite:///tutorial.db', echo=True)

# テーブル作成
Base.metadata.create_all(engine)

print("✅ テーブルが作成されました")
```

### 2. 複数のモデル

```python
class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default="CURRENT_TIMESTAMP"
    )

class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )
```

## まとめ

- `DeclarativeBase`でベースクラスを定義
- `Mapped[T]`で型安全なモデル定義
- `mapped_column()`でカラムのオプションを指定
- `create_all()`でテーブルを一括作成
- Python型は自動的にSQL型にマッピングされる

次の章では、これらのモデルを使ったCRUD操作を学びます。
