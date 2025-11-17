# 第17章: データベース固有機能

PostgreSQL、MySQL、SQLiteなどのデータベース固有機能をSQLAlchemyで使用する方法を学びます。

## PostgreSQL固有機能

### ARRAY型

```python
from sqlalchemy.dialects.postgresql import ARRAY

class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(primary_key=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String))

# 使用例
article = Article(tags=['python', 'sqlalchemy', 'database'])

# クエリ
stmt = select(Article).where(Article.tags.contains(['python']))
stmt = select(Article).where(Article.tags.any('python'))
```

### JSON/JSONB型

```python
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    preferences: Mapped[dict] = mapped_column(JSONB)

# JSON操作
user.preferences = {"theme": "dark", "language": "ja"}

# JSONパスでクエリ
stmt = select(User).where(
    User.preferences['theme'].astext == 'dark'
)
```

### UUID型

```python
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Record(Base):
    __tablename__ = 'records'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
```

### Full Text Search

```python
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TSVECTOR

# 全文検索
stmt = select(Article).where(
    func.to_tsvector('english', Article.content).match('python & database')
)
```

## MySQL固有機能

### ENUM型

```python
import enum
from sqlalchemy import Enum

class Status(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(Base):
    __tablename__ = 'applications'

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[Status] = mapped_column(Enum(Status))
```

### AUTO_INCREMENT設定

```python
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4'
    }
```

## SQLite固有機能

### 外部キー有効化

```python
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

## 全データベース共通のベストプラクティス

### スキーマ指定

```python
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}  # PostgreSQL
```

### 方言別の処理

```python
from sqlalchemy import func

if engine.dialect.name == 'postgresql':
    # PostgreSQL固有の処理
    stmt = select(func.now())
elif engine.dialect.name == 'mysql':
    # MySQL固有の処理
    stmt = select(func.current_timestamp())
```

詳細は各データベースの公式ドキュメントとSQLAlchemyの方言ドキュメントを参照してください。
