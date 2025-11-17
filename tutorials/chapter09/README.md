# 第9章: Hybrid PropertiesとExpression

## 学習目標
- Hybrid Propertyの概念と用途を理解する
- Pythonレベルとデータベースレベルの両方で動作する属性を作成する
- カスタムSQL式を定義する方法を学ぶ
- Hybrid Methodの使い方を習得する

## Hybrid Propertyとは

**Hybrid Property**は、Pythonのインスタンスレベルとクラスレベル（SQL式）の両方で動作する属性です。

### 通常のPropertyとの違い

```python
# 通常のProperty
class User(Base):
    __tablename__ = 'users'
    first_name: Mapped[str]
    last_name: Mapped[str]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# ❌ クエリで使えない
stmt = select(User).where(User.full_name == "Alice Smith")  # エラー！
```

```python
# Hybrid Property
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

class User(Base):
    __tablename__ = 'users'
    first_name: Mapped[str]
    last_name: Mapped[str]

    @hybrid_property
    def full_name(self):
        # Pythonレベル
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        # SQLレベル
        return cls.first_name + ' ' + cls.last_name

# ✅ クエリで使える！
stmt = select(User).where(User.full_name == "Alice Smith")
# SELECT ... WHERE first_name || ' ' || last_name = 'Alice Smith'
```

## Hybrid Propertyの基本

### 単純な計算プロパティ

```python
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, date

class Person(Base):
    __tablename__ = 'persons'

    id: Mapped[int] = mapped_column(primary_key=True)
    birth_date: Mapped[date]

    @hybrid_property
    def age(self):
        """Pythonレベル: インスタンスから年齢を計算"""
        today = date.today()
        return today.year - self.birth_date.year

    @age.expression
    def age(cls):
        """SQLレベル: SQL式で年齢を計算"""
        from sqlalchemy import extract, func
        return extract('year', func.current_date()) - extract('year', cls.birth_date)

# 使用例
with Session(engine) as session:
    # Pythonレベル
    person = session.get(Person, 1)
    print(f"年齢: {person.age}")  # Pythonで計算

    # SQLレベル
    stmt = select(Person).where(Person.age >= 18)
    adults = session.execute(stmt).scalars().all()
    # SELECT ... WHERE (EXTRACT(year FROM current_date()) - EXTRACT(year FROM birth_date)) >= 18
```

### 文字列操作

```python
class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)

    @hybrid_property
    def preview(self):
        """最初の100文字を返す"""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

    @preview.expression
    def preview(cls):
        """SQL式で最初の100文字"""
        from sqlalchemy import func, case
        return case(
            (func.length(cls.content) > 100, func.substr(cls.content, 1, 100) + '...'),
            else_=cls.content
        )
```

### ブール値の計算

```python
from decimal import Decimal

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[Decimal] = mapped_column()
    discount_price: Mapped[Optional[Decimal]] = mapped_column()

    @hybrid_property
    def is_on_sale(self):
        """割引中かどうか"""
        return self.discount_price is not None and self.discount_price < self.price

    @is_on_sale.expression
    def is_on_sale(cls):
        """SQL式で割引判定"""
        from sqlalchemy import and_
        return and_(
            cls.discount_price.isnot(None),
            cls.discount_price < cls.price
        )

# 使用例
stmt = select(Product).where(Product.is_on_sale == True)
# SELECT ... WHERE discount_price IS NOT NULL AND discount_price < price
```

## Hybrid Method

メソッド（引数を取る）版のHybrid Propertyです。

### 基本的な使い方

```python
from sqlalchemy.ext.hybrid import hybrid_method

class Interval(Base):
    __tablename__ = 'intervals'

    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[int]
    end: Mapped[int]

    @hybrid_method
    def contains(self, point: int):
        """Pythonレベル: 値が範囲内か判定"""
        return self.start <= point < self.end

    @contains.expression
    def contains(cls, point: int):
        """SQLレベル: SQL式で範囲判定"""
        from sqlalchemy import and_
        return and_(cls.start <= point, point < cls.end)

# 使用例
with Session(engine) as session:
    # Pythonレベル
    interval = session.get(Interval, 1)
    print(interval.contains(5))  # True/False

    # SQLレベル
    stmt = select(Interval).where(Interval.contains(5))
    # SELECT ... WHERE start <= 5 AND 5 < end
```

### 複雑な検索メソッド

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

    @hybrid_method
    def search(self, keyword: str):
        """Pythonレベル: 名前またはメールに含まれるか"""
        keyword = keyword.lower()
        return keyword in self.name.lower() or keyword in self.email.lower()

    @search.expression
    def search(cls, keyword: str):
        """SQLレベル: SQL式で検索"""
        from sqlalchemy import or_, func
        keyword = f"%{keyword}%"
        return or_(
            func.lower(cls.name).like(func.lower(keyword)),
            func.lower(cls.email).like(func.lower(keyword))
        )

# 使用例
stmt = select(User).where(User.search("alice"))
# SELECT ... WHERE lower(name) LIKE lower('%alice%') OR lower(email) LIKE lower('%alice%')
```

## 複雑なExpression

### 複数カラムの組み合わせ

```python
from sqlalchemy import case, func

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    subtotal: Mapped[Decimal] = mapped_column()
    tax_rate: Mapped[Decimal] = mapped_column()
    discount: Mapped[Decimal] = mapped_column(default=Decimal('0'))

    @hybrid_property
    def total(self):
        """合計金額を計算"""
        tax = self.subtotal * self.tax_rate
        return self.subtotal + tax - self.discount

    @total.expression
    def total(cls):
        """SQL式で合計計算"""
        tax = cls.subtotal * cls.tax_rate
        return cls.subtotal + tax - cls.discount

    @hybrid_property
    def discount_percentage(self):
        """割引率（%）"""
        if self.subtotal == 0:
            return 0
        return (self.discount / self.subtotal) * 100

    @discount_percentage.expression
    def discount_percentage(cls):
        """SQL式で割引率計算"""
        return case(
            (cls.subtotal == 0, 0),
            else_=(cls.discount / cls.subtotal) * 100
        )
```

### サブクエリを使った式

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[List["Post"]] = relationship(back_populates="user")

    @hybrid_property
    def post_count(self):
        """Pythonレベル: 投稿数"""
        return len(self.posts)

    @post_count.expression
    def post_count(cls):
        """SQLレベル: サブクエリで投稿数を取得"""
        from sqlalchemy import select, func
        return (
            select(func.count(Post.id))
            .where(Post.user_id == cls.id)
            .correlate_except(Post)
            .scalar_subquery()
        )

# 使用例
stmt = select(User).where(User.post_count > 10)
# SELECT ... WHERE (SELECT count(posts.id) FROM posts WHERE posts.user_id = users.id) > 10
```

## Comparatorのカスタマイズ

より高度な比較演算子を定義できます。

```python
from sqlalchemy.ext.hybrid import Comparator

class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)

    def __ne__(self, other):
        return func.lower(self.__clause_element__()) != func.lower(other)

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    _email: Mapped[str] = mapped_column("email", String(100))

    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value.lower()

    @email.comparator
    def email(cls):
        return CaseInsensitiveComparator(cls._email)

# 使用例
stmt = select(User).where(User.email == "ALICE@EXAMPLE.COM")
# SELECT ... WHERE lower(email) = lower('ALICE@EXAMPLE.COM')
```

## 実践例: Eコマースモデル

```python
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    regular_price: Mapped[Decimal] = mapped_column()
    sale_price: Mapped[Optional[Decimal]] = mapped_column()
    stock: Mapped[int] = mapped_column()
    cost: Mapped[Decimal] = mapped_column()

    @hybrid_property
    def current_price(self):
        """現在の価格（セール中ならセール価格）"""
        return self.sale_price if self.sale_price else self.regular_price

    @current_price.expression
    def current_price(cls):
        from sqlalchemy import case
        return case(
            (cls.sale_price.isnot(None), cls.sale_price),
            else_=cls.regular_price
        )

    @hybrid_property
    def profit_margin(self):
        """利益率（%）"""
        price = self.current_price
        if price == 0:
            return Decimal('0')
        return ((price - self.cost) / price) * 100

    @profit_margin.expression
    def profit_margin(cls):
        price = cls.current_price
        return case(
            (price == 0, 0),
            else_=((price - cls.cost) / price) * 100
        )

    @hybrid_property
    def in_stock(self):
        """在庫ありか"""
        return self.stock > 0

    @in_stock.expression
    def in_stock(cls):
        return cls.stock > 0

# クエリ例
with Session(engine) as session:
    # 利益率30%以上の商品
    stmt = select(Product).where(Product.profit_margin >= 30)

    # 在庫があってセール中の商品
    stmt = select(Product).where(
        Product.in_stock == True,
        Product.sale_price.isnot(None)
    )

    # 現在価格でソート
    stmt = select(Product).order_by(Product.current_price.desc())
```

## ベストプラクティス

### 1. パフォーマンスを考慮

```python
# ❌ 重い計算をHybrid Propertyに
@hybrid_property
def expensive_calculation(self):
    # 複雑な計算...
    return result

# ✅ 必要な時だけ計算するメソッドに
def calculate_expensive(self):
    # 複雑な計算...
    return result
```

### 2. NULL対策

```python
@hybrid_property
def safe_division(self):
    if self.denominator == 0:
        return 0
    return self.numerator / self.denominator

@safe_division.expression
def safe_division(cls):
    from sqlalchemy import case
    return case(
        (cls.denominator == 0, 0),
        else_=cls.numerator / cls.denominator
    )
```

### 3. 型の一貫性

```python
@hybrid_property
def score(self) -> int:  # 型ヒント
    return int(self.points / 10)

@score.expression
def score(cls):
    from sqlalchemy import cast, Integer
    return cast(cls.points / 10, Integer)
```

## まとめ

- **Hybrid Property**: Pythonレベルとクエリレベルの両方で動作
- `@hybrid_property`と`@property.expression`で定義
- **Hybrid Method**: 引数を取るHybrid Property
- サブクエリや複雑な式も定義可能
- カスタムComparatorで比較演算子を拡張

次の章では、イベントシステムについて学びます。
