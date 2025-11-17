# 第14章: ReflectionとInspection

既存のデータベースからスキーマを読み取り、動的にモデルを生成する方法を学びます。

## Reflection

既存のデータベーステーブルを自動的にマッピングします。

```python
from sqlalchemy import MetaData, Table

metadata = MetaData()

# テーブルを反映
users_table = Table('users', metadata, autoload_with=engine)

# カラム情報を取得
for column in users_table.columns:
    print(f"{column.name}: {column.type}")

# クエリ実行
from sqlalchemy import select
stmt = select(users_table)
with engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(row)
```

## 全テーブルの反映

```python
metadata = MetaData()
metadata.reflect(bind=engine)

# 全テーブルにアクセス
for table_name in metadata.tables:
    table = metadata.tables[table_name]
    print(f"Table: {table_name}")
    for column in table.columns:
        print(f"  {column.name}: {column.type}")
```

## Inspector

データベースのメタ情報を調査します。

```python
from sqlalchemy import inspect

inspector = inspect(engine)

# テーブル一覧
table_names = inspector.get_table_names()
print(f"テーブル: {table_names}")

# カラム情報
columns = inspector.get_columns('users')
for col in columns:
    print(f"{col['name']}: {col['type']}")

# 外部キー
foreign_keys = inspector.get_foreign_keys('posts')
for fk in foreign_keys:
    print(f"FK: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

# インデックス
indexes = inspector.get_indexes('users')
for idx in indexes:
    print(f"Index: {idx['name']} on {idx['column_names']}")
```

## Automap

Reflectionから自動的にORMクラスを生成します。

```python
from sqlalchemy.ext.automap import automap_base

Base = automap_base()
Base.prepare(autoload_with=engine)

# 自動生成されたクラス
User = Base.classes.users
Post = Base.classes.posts

# 通常のORMとして使用
with Session(engine) as session:
    users = session.query(User).all()
```

Reflectionは既存のレガシーデータベースを扱う際に非常に便利です。
