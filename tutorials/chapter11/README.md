# 第11章: 継承とポリモーフィズム

## 学習目標
- SQLAlchemyでの継承パターンを理解する
- Single Table Inheritance (単一テーブル継承)
- Joined Table Inheritance (結合テーブル継承)
- Concrete Table Inheritance (具象テーブル継承)
- ポリモーフィッククエリの実装方法

## 継承の3つのパターン

SQLAlchemyは、オブジェクト指向の継承をデータベースに マッピングする3つの戦略をサポートしています。

### パターン比較

```
Single Table Inheritance (STI)
┌────────────────────────────────┐
│ employees table                │
├────┬───────┬──────┬────────────┤
│ id │ type  │ name │ manager_id │← managerだけ使用
│ id │ type  │ name │ NULL       │
└────┴───────┴──────┴────────────┘
  ✅ シンプル、高速
  ❌ NULLカラムが多い

Joined Table Inheritance
┌─────────────┐  ┌───────────────────┐
│ employees   │  │ managers          │
├────┬────────┤  ├────┬──────────────┤
│ id │ name   │  │ id │ department   │
└────┴────────┘  └────┴──────────────┘
        △               △
        └───────────────┘ JOIN
  ✅ 正規化、NULLなし
  ❌ JOIN必要、遅い

Concrete Table Inheritance
┌──────────────┐  ┌─────────────────┐
│ engineers    │  │ managers        │
├────┬─────────┤  ├────┬────────────┤
│ id │ name    │  │ id │ name       │
│    │ lang    │  │    │ department │
└────┴─────────┘  └────┴────────────┘
  ✅ 独立、高速
  ❌ 重複カラム、ポリモーフィッククエリ複雑
```

## Single Table Inheritance

全てのサブクラスを1つのテーブルに格納します。

### モデル定義

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'employee',
        'polymorphic_on': type
    }

class Engineer(Employee):
    """エンジニア（サブクラス）"""
    programming_language: Mapped[Optional[str]] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'engineer'
    }

class Manager(Employee):
    """マネージャー（サブクラス）"""
    department: Mapped[Optional[str]] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'manager'
    }
```

### 使用例

```python
with Session(engine) as session:
    # 各サブクラスを作成
    engineer = Engineer(name="Alice", programming_language="Python")
    manager = Manager(name="Bob", department="Engineering")

    session.add_all([engineer, manager])
    session.commit()

    # ポリモーフィッククエリ（全従業員）
    stmt = select(Employee)
    employees = session.execute(stmt).scalars().all()
    # [<Engineer>, <Manager>]

    # 特定のサブクラスのみ
    stmt = select(Engineer)
    engineers = session.execute(stmt).scalars().all()
    # [<Engineer>]

    # 型チェック
    for emp in employees:
        if isinstance(emp, Engineer):
            print(f"{emp.name}: {emp.programming_language}")
        elif isinstance(emp, Manager):
            print(f"{emp.name}: {emp.department}")
```

### 生成されるテーブル

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50),  -- 'employee', 'engineer', 'manager'
    name VARCHAR(100),
    programming_language VARCHAR(50),  -- engineerのみ使用
    department VARCHAR(50)  -- managerのみ使用
);
```

## Joined Table Inheritance

各サブクラスが独自のテーブルを持ち、JOINで結合します。

### モデル定義

```python
class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'employee',
        'polymorphic_on': type,
        'with_polymorphic': '*'  # 常にJOIN
    }

class Engineer(Employee):
    __tablename__ = 'engineers'

    id: Mapped[int] = mapped_column(ForeignKey('employees.id'), primary_key=True)
    programming_language: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'engineer'
    }

class Manager(Employee):
    __tablename__ = 'managers'

    id: Mapped[int] = mapped_column(ForeignKey('employees.id'), primary_key=True)
    department: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'manager'
    }
```

### 生成されるSQL

```sql
-- 親テーブル
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50),
    name VARCHAR(100)
);

-- 子テーブル
CREATE TABLE engineers (
    id INTEGER PRIMARY KEY,
    programming_language VARCHAR(50),
    FOREIGN KEY(id) REFERENCES employees(id)
);

CREATE TABLE managers (
    id INTEGER PRIMARY KEY,
    department VARCHAR(50),
    FOREIGN KEY(id) REFERENCES employees(id)
);
```

### クエリ

```python
# ポリモーフィッククエリ（自動的にJOIN）
stmt = select(Employee)
# SELECT employees.*, engineers.*, managers.*
# FROM employees
# LEFT OUTER JOIN engineers ON employees.id = engineers.id
# LEFT OUTER JOIN managers ON employees.id = managers.id
```

## Concrete Table Inheritance

各サブクラスが完全に独立したテーブルを持ちます。

### モデル定義

```python
class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'employee',
        'concrete': True
    }

class Engineer(Employee):
    __tablename__ = 'engineers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    programming_language: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'engineer',
        'concrete': True
    }

class Manager(Employee):
    __tablename__ = 'managers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    department: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'manager',
        'concrete': True
    }
```

### UNIONクエリ

```python
# ポリモーフィッククエリ（UNION使用）
from sqlalchemy.orm import with_polymorphic

poly = with_polymorphic(Employee, [Engineer, Manager])
stmt = select(poly)
# SELECT ... FROM (
#   SELECT id, name, NULL as programming_language, NULL as department, 'employee' as type FROM employees
#   UNION ALL
#   SELECT id, name, programming_language, NULL, 'engineer' FROM engineers
#   UNION ALL
#   SELECT id, name, NULL, department, 'manager' FROM managers
# )
```

## パターンの選択基準

### Single Table - こんな時に使う

```python
# ✅ サブクラスの違いが小さい
# ✅ パフォーマンスが重要
# ✅ クエリが頻繁

class Vehicle(Base):
    __tablename__ = 'vehicles'
    # type, make, model, color...

class Car(Vehicle):
    # doors, trunk_size
    pass

class Motorcycle(Vehicle):
    # engine_type
    pass
```

### Joined Table - こんな時に使う

```python
# ✅ サブクラス固有の属性が多い
# ✅ NULLを避けたい
# ✅ データ整合性が重要

class Content(Base):
    __tablename__ = 'content'
    # id, title, created_at

class Article(Content):
    __tablename__ = 'articles'
    # body, word_count, reading_time

class Video(Content):
    __tablename__ = 'videos'
    # url, duration, thumbnail, format
```

### Concrete Table - こんな時に使う

```python
# ✅ サブクラスが完全に独立
# ✅ ポリモーフィッククエリが少ない
# ✅ 各テーブルのパフォーマンス最適化が必要

class Payment(Base):
    # 決済の基底クラス（抽象的）
    pass

class CreditCardPayment(Payment):
    __tablename__ = 'credit_card_payments'
    # card_number, cvv, expiry...

class BankTransferPayment(Payment):
    __tablename__ = 'bank_transfers'
    # account_number, routing_number...
```

## with_polymorphicの使い方

特定のサブクラスだけを先行読み込みします。

```python
# 全サブクラス
poly_all = with_polymorphic(Employee, '*')
stmt = select(poly_all)

# 特定のサブクラスのみ
poly_specific = with_polymorphic(Employee, [Engineer])
stmt = select(poly_specific)

# エイリアスを使用
eng = aliased(Engineer)
stmt = select(eng).where(eng.programming_language == 'Python')
```

## 実践例: CMSのコンテンツ管理

```python
from datetime import datetime
from sqlalchemy import Text

class Content(Base):
    """全コンテンツの基底クラス"""
    __tablename__ = 'content'

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    published: Mapped[bool] = mapped_column(default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'polymorphic_on': type
    }

class Article(Content):
    """記事"""
    body: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column()
    reading_time: Mapped[int] = mapped_column()  # 分

    __mapper_args__ = {
        'polymorphic_identity': 'article'
    }

class Video(Content):
    """動画"""
    video_url: Mapped[str] = mapped_column(String(500))
    duration: Mapped[int] = mapped_column()  # 秒
    thumbnail_url: Mapped[str] = mapped_column(String(500))

    __mapper_args__ = {
        'polymorphic_identity': 'video'
    }

class Gallery(Content):
    """画像ギャラリー"""
    image_count: Mapped[int] = mapped_column()

    __mapper_args__ = {
        'polymorphic_identity': 'gallery'
    }

# 使用例
with Session(engine) as session:
    # 公開済みコンテンツを全て取得
    stmt = select(Content).where(Content.published == True)
    all_content = session.execute(stmt).scalars().all()

    for content in all_content:
        if isinstance(content, Article):
            print(f"記事: {content.title} ({content.reading_time}分)")
        elif isinstance(content, Video):
            print(f"動画: {content.title} ({content.duration}秒)")
        elif isinstance(content, Gallery):
            print(f"ギャラリー: {content.title} ({content.image_count}枚)")
```

## まとめ

- **Single Table**: 1テーブル、高速、NULLあり
- **Joined Table**: 正規化、JOIN必要
- **Concrete Table**: 独立、UNION必要
- `polymorphic_identity`でサブクラスを識別
- `with_polymorphic`で先行読み込み

次の章では、Association ProxyとOrdering Listについて学びます。
