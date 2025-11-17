# 第12章: Association ProxyとOrdering List

Association Proxyは多対多リレーションシップを簡略化し、Ordering Listはリストの順序を管理します。これらの高度な機能を学びます。

## Association Proxy

多対多リレーションシップの中間テーブルを透過的に扱えるようにします。

### 通常の多対多（中間テーブルあり）

```python
# 中間テーブル
user_keywords = Table('user_keywords', Base.metadata,
    Column('user_id', ForeignKey('users.id')),
    Column('keyword_id', ForeignKey('keywords.id'))
)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    keywords: Mapped[List["Keyword"]] = relationship(secondary=user_keywords)

# ❌ 使いにくい
user.keywords.append(Keyword(name="python"))
keyword_names = [k.name for k in user.keywords]
```

### Association Proxyを使用

```python
from sqlalchemy.ext.associationproxy import association_proxy

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    _keywords: Mapped[List["Keyword"]] = relationship(secondary=user_keywords)

    # ✅ Proxyで簡単にアクセス
    keyword_names = association_proxy('_keywords', 'name')

# 使用例
user.keyword_names = ['python', 'sqlalchemy']  # 自動的にKeywordオブジェクト作成
print(user.keyword_names)  # ['python', 'sqlalchemy']
```

## Ordering List

リストの順序をデータベースで管理します。

```python
from sqlalchemy.ext.orderinglist import ordering_list

class TodoList(Base):
    __tablename__ = 'todo_lists'
    id: Mapped[int] = mapped_column(primary_key=True)
    items: Mapped[List["TodoItem"]] = relationship(
        order_by="TodoItem.position",
        collection_class=ordering_list('position')
    )

class TodoItem(Base):
    __tablename__ = 'todo_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey('todo_lists.id'))
    text: Mapped[str]
    position: Mapped[int]

# 使用例
todo = TodoList()
todo.items.append(TodoItem(text="Task 1"))  # position=0
todo.items.append(TodoItem(text="Task 2"))  # position=1
todo.items.insert(0, TodoItem(text="Urgent"))  # position=0, 他が自動的にシフト
```

詳細は公式ドキュメントを参照してください。
