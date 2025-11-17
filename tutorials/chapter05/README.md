# 第5章: リレーションシップとJOIN

## 学習目標
- テーブル間のリレーションシップを理解する
- 1対多、多対多の関係を定義できる
- 外部キーの仕組みを理解する
- JOINクエリを効率的に実行できる

## リレーションシップとは

リレーションシップは、テーブル間の関係を定義します。

### 主な関係性

```
1対多 (One-to-Many)
User ─────< Post
1人のユーザーが複数の投稿を持つ

多対1 (Many-to-One)
Post >───── User
複数の投稿が1人のユーザーに属する

多対多 (Many-to-Many)
Student ><──── Course
      association_table

1対1 (One-to-One)
User ───── Profile
1人のユーザーに1つのプロフィール
```

## 1対多リレーションシップ

### 例: UserとPost

```
users テーブル              posts テーブル
┌──────┬─────────┐         ┌──────┬─────────┬─────────┐
│ id   │ name    │         │ id   │ title   │ user_id │
├──────┼─────────┤         ├──────┼─────────┼─────────┤
│ 1    │ Alice   │<────┐   │ 1    │ Post A  │ 1       │
│ 2    │ Bob     │     │   │ 2    │ Post B  │ 1       │
└──────┴─────────┘     │   │ 3    │ Post C  │ 2       │
                       └───│ 4    │ Post D  │ 1       │
                           └──────┴─────────┴─────────┘
                                          外部キー
```

### モデル定義

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    # リレーションシップ（1対多の"1"側）
    posts: Mapped[List["Post"]] = relationship(back_populates="user")

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))

    # 外部キー（多側が持つ）
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # リレーションシップ（1対多の"多"側）
    user: Mapped["User"] = relationship(back_populates="posts")
```

### リレーションシップの構成要素

```python
posts: Mapped[List["Post"]] = relationship(back_populates="user")
│      │     │     │          │            │
│      │     │     │          │            └─ 相手側の属性名
│      │     │     │          └────────────── relationshipの設定
│      │     │     └───────────────────────── 関連モデル（文字列でOK）
│      │     └─────────────────────────────── Listで複数を示す
│      └───────────────────────────────────── Mapped型
└──────────────────────────────────────────── 属性名
```

### 使用例

```python
with Session(engine) as session:
    # ユーザーを作成
    user = User(name="Alice")

    # 投稿を作成してユーザーに関連付け
    post1 = Post(title="First Post", user=user)
    post2 = Post(title="Second Post", user=user)

    session.add(user)
    session.commit()

    # ユーザーから投稿を取得
    print(f"{user.name}の投稿:")
    for post in user.posts:
        print(f"  - {post.title}")

    # 投稿からユーザーを取得
    print(f"'{post1.title}'の作者: {post1.user.name}")
```

## 外部キー制約

### 外部キーの動作

```python
# CASCADE: 親を削除すると子も削除
class Post(Base):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

# SET NULL: 親を削除すると子の外部キーをNULLに
class Post(Base):
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

# RESTRICT: 子が存在する場合、親を削除できない（デフォルト）
class Post(Base):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
```

### 図解: CASCADE動作

```
削除前:
User(id=1) ──┬── Post(id=1, user_id=1)
             ├── Post(id=2, user_id=1)
             └── Post(id=3, user_id=1)

session.delete(user)  # ondelete="CASCADE"の場合
↓

削除後:
（すべて削除される）
```

## Lazy Loading vs Eager Loading

### Lazy Loading（遅延読み込み）

デフォルトの動作。関連オブジェクトは、アクセス時に読み込まれます。

```python
with Session(engine) as session:
    user = session.get(User, 1)
    # この時点では SELECT * FROM users WHERE id = 1

    print(user.posts)  # ← ここで初めてpostsを読み込む
    # SELECT * FROM posts WHERE user_id = 1
```

**問題: N+1クエリ**

```python
users = session.execute(select(User)).scalars().all()  # 1クエリ

for user in users:  # 100ユーザーいたら...
    print(user.posts)  # 100クエリ発行！
# 合計101クエリ！
```

### Eager Loading（先行読み込み）

関連オブジェクトを事前に読み込みます。

#### 1. joinedload（JOIN方式）

```python
from sqlalchemy.orm import joinedload

stmt = select(User).options(joinedload(User.posts))
users = session.execute(stmt).unique().scalars().all()

# 発行されるSQL:
# SELECT users.*, posts.*
# FROM users
# LEFT OUTER JOIN posts ON users.id = posts.user_id
```

**メリット**: 1クエリで完結
**デメリット**: 多対多で大量のデータがある場合、重複が多い

#### 2. selectinload（IN方式）

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.posts))
users = session.execute(stmt).scalars().all()

# 発行されるSQL:
# SELECT * FROM users
# SELECT * FROM posts WHERE user_id IN (1, 2, 3, ...)
```

**メリット**: 重複なし、2クエリで完結
**デメリット**: JOINより若干遅い

### Eager Loadingの比較

```
┌─────────────────────────────────────────┐
│ joinedload                              │
├─────────────────────────────────────────┤
│ SELECT users.id, users.name,            │
│        posts.id, posts.title, ...       │
│ FROM users                              │
│ LEFT OUTER JOIN posts ON ...            │
├─────────────────────────────────────────┤
│ ✅ 1クエリで完結                         │
│ ❌ 重複データが多い                      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ selectinload                            │
├─────────────────────────────────────────┤
│ 1. SELECT * FROM users                  │
│ 2. SELECT * FROM posts                  │
│    WHERE user_id IN (1, 2, 3, ...)      │
├─────────────────────────────────────────┤
│ ✅ 重複なし                              │
│ ✅ 大量データに強い                      │
│ ❌ 2クエリ必要                           │
└─────────────────────────────────────────┘
```

## 多対多リレーションシップ

### 例: StudentとCourse

```
students              student_courses         courses
┌────┬──────┐        ┌────────┬─────────┐   ┌────┬────────┐
│ id │ name │        │ student│ course  │   │ id │ name   │
├────┼──────┤        │ _id    │ _id     │   ├────┼────────┤
│ 1  │ Alice│<───┬───│ 1      │ 101     │───>│101 │ Math   │
│ 2  │ Bob  │    │   │ 1      │ 102     │   │102 │ Physics│
└────┴──────┘    │   │ 2      │ 101     │   └────┴────────┘
                 └───│ 2      │ 103     │
                     └────────┴─────────┘
                     中間テーブル
```

### モデル定義

```python
from sqlalchemy import Table, Column, ForeignKey

# 中間テーブル（Tableオブジェクトとして定義）
student_courses = Table(
    'student_courses',
    Base.metadata,
    Column('student_id', ForeignKey('students.id'), primary_key=True),
    Column('course_id', ForeignKey('courses.id'), primary_key=True)
)

class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    # 多対多リレーションシップ
    courses: Mapped[List["Course"]] = relationship(
        secondary=student_courses,
        back_populates="students"
    )

class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    students: Mapped[List["Student"]] = relationship(
        secondary=student_courses,
        back_populates="courses"
    )
```

### 使用例

```python
with Session(engine) as session:
    # 学生とコースを作成
    alice = Student(name="Alice")
    bob = Student(name="Bob")

    math = Course(name="Math")
    physics = Course(name="Physics")

    # 関連付け
    alice.courses.append(math)
    alice.courses.append(physics)
    bob.courses.append(math)

    session.add_all([alice, bob, math, physics])
    session.commit()

    # 学生のコースを表示
    for student in [alice, bob]:
        print(f"{student.name}の受講コース:")
        for course in student.courses:
            print(f"  - {course.name}")
```

## 実践ハンズオン

`01_relationships.py`を作成:

```python
from sqlalchemy import create_engine, ForeignKey, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import relationship, Session
from typing import List

class Base(DeclarativeBase):
    pass

# 1対多の例
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

# テーブル作成
engine = create_engine('sqlite:///tutorial.db', echo=True)
Base.metadata.create_all(engine)

# データ投入
with Session(engine) as session:
    alice = User(name="Alice")
    alice.posts.append(Post(title="First Post"))
    alice.posts.append(Post(title="Second Post"))

    session.add(alice)
    session.commit()

# データ取得
with Session(engine) as session:
    user = session.get(User, 1)
    print(f"\n{user.name}の投稿:")
    for post in user.posts:
        print(f"  - {post.title}")
```

## まとめ

- **1対多**: `relationship()`と`ForeignKey`で定義
- **多対多**: 中間テーブル（`secondary`）を使用
- **Lazy Loading**: アクセス時に読み込み（N+1問題に注意）
- **Eager Loading**: `joinedload`/`selectinload`で事前読み込み
- 外部キー制約で参照整合性を保証

次の章では、より高度なクエリとCore APIについて学びます。
