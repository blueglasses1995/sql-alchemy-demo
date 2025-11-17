# 第15章: CTE、Window関数、高度なSQL

SQLAlchemy 2.0で使える高度なSQL機能を学びます。

## CTE (Common Table Expression)

WITH句を使った共通テーブル式です。

```python
from sqlalchemy import select, func

# 基本的なCTE
user_counts = (
    select(
        Post.user_id,
        func.count(Post.id).label('post_count')
    )
    .group_by(Post.user_id)
    .cte('user_counts')
)

# CTEを使ったクエリ
stmt = (
    select(User.name, user_counts.c.post_count)
    .join(user_counts, User.id == user_counts.c.user_id)
    .where(user_counts.c.post_count > 10)
)

# SQL:
# WITH user_counts AS (
#   SELECT user_id, COUNT(id) as post_count
#   FROM posts GROUP BY user_id
# )
# SELECT users.name, user_counts.post_count
# FROM users JOIN user_counts ON users.id = user_counts.user_id
# WHERE user_counts.post_count > 10
```

## 再帰CTE

階層データの処理に便利です。

```python
# カテゴリツリーの例
class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey('categories.id'))

# 再帰CTE
included = (
    select(Category.id, Category.name, Category.parent_id)
    .where(Category.id == 1)  # ルートカテゴリ
    .cte('included', recursive=True)
)

# 再帰部分
included_alias = included.alias()
categories_alias = Category.__table__.alias()

included = included.union_all(
    select(categories_alias.c.id, categories_alias.c.name, categories_alias.c.parent_id)
    .where(categories_alias.c.parent_id == included_alias.c.id)
)

# 実行
stmt = select(included)
# 全サブカテゴリを再帰的に取得
```

## Window関数

行をグループ化せずに集約を行います。

### ROW_NUMBER

```python
from sqlalchemy import over

stmt = select(
    User.name,
    User.score,
    func.row_number().over(
        order_by=User.score.desc()
    ).label('rank')
)

# SELECT name, score, ROW_NUMBER() OVER (ORDER BY score DESC) as rank
# FROM users
```

### RANK / DENSE_RANK

```python
stmt = select(
    User.name,
    User.department,
    User.salary,
    func.rank().over(
        partition_by=User.department,
        order_by=User.salary.desc()
    ).label('dept_rank')
)

# SELECT name, department, salary,
#   RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
# FROM users
```

### LAG / LEAD

```python
# 前の行/次の行の値を取得
stmt = select(
    Sale.date,
    Sale.amount,
    func.lag(Sale.amount).over(
        order_by=Sale.date
    ).label('prev_amount'),
    func.lead(Sale.amount).over(
        order_by=Sale.date
    ).label('next_amount')
)
```

## UNION / INTERSECT / EXCEPT

```python
from sqlalchemy import union, intersect, except_

# UNION
stmt1 = select(User.email).where(User.is_active == True)
stmt2 = select(Admin.email).where(Admin.is_active == True)

combined = union(stmt1, stmt2)

# INTERSECT (共通部分)
common = intersect(stmt1, stmt2)

# EXCEPT (差集合)
difference = except_(stmt1, stmt2)
```

## サブクエリ

### Scalar Subquery

```python
# ユーザーごとの最新投稿日
latest_post = (
    select(func.max(Post.created_at))
    .where(Post.user_id == User.id)
    .scalar_subquery()
)

stmt = select(User.name, latest_post.label('latest_post_date'))
```

### Lateral Subquery

```python
# PostgreSQL専用
from sqlalchemy import lateral

# 各ユーザーの最新3件の投稿
latest_posts = (
    select(Post)
    .where(Post.user_id == User.id)
    .order_by(Post.created_at.desc())
    .limit(3)
    .lateral('latest_posts')
)

stmt = select(User, latest_posts).join(latest_posts, true())
```

## CASE文

```python
from sqlalchemy import case

# CASE式
age_group = case(
    (User.age < 18, 'minor'),
    (User.age < 65, 'adult'),
    else_='senior'
).label('age_group')

stmt = select(User.name, age_group)

# SELECT name,
#   CASE
#     WHEN age < 18 THEN 'minor'
#     WHEN age < 65 THEN 'adult'
#     ELSE 'senior'
#   END as age_group
# FROM users
```

## 集約ウィンドウ関数

```python
# 累積合計
stmt = select(
    Sale.date,
    Sale.amount,
    func.sum(Sale.amount).over(
        order_by=Sale.date
    ).label('cumulative_total')
)

# 移動平均
stmt = select(
    Sale.date,
    Sale.amount,
    func.avg(Sale.amount).over(
        order_by=Sale.date,
        rows=(2, 0)  # 過去2行を含む3行の平均
    ).label('moving_avg')
)
```

詳細な使い方は公式ドキュメントを参照してください。
