# 第2章: データベース接続とエンジン

## 学習目標
- Engineの役割と動作原理を理解する
- コネクションプールの仕組みを理解する
- 各種データベースへの接続方法を学ぶ
- 実際に接続してクエリを実行する

## Engineとは

**Engine**はSQLAlchemyの中核となるコンポーネントで、データベース接続を管理します。

### Engineの役割

```
┌──────────────────────────────────────┐
│         SQLAlchemy Engine            │
│  ┌────────────────────────────────┐  │
│  │   Connection Pool              │  │
│  │  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐    │  │
│  │  │C1│ │C2│ │C3│ │C4│ │C5│    │  │
│  │  └──┘ └──┘ └──┘ └──┘ └──┘    │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │   Dialect (方言)               │  │
│  │   - SQLite                     │  │
│  │   - PostgreSQL                 │  │
│  │   - MySQL                      │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
              │
              ▼
    ┌─────────────────┐
    │  DBAPI Driver   │
    │  (PEP 249)      │
    └─────────────────┘
              │
              ▼
        データベース
```

1. **Connection Pool管理**: 接続の再利用と効率化
2. **Dialect選択**: データベース固有のSQL方言を吸収
3. **トランザクション管理**: BEGIN/COMMIT/ROLLBACKの制御

## Engineの作成

### 基本的な構文

```python
from sqlalchemy import create_engine

# 一般的な形式
engine = create_engine('dialect+driver://user:pass@host:port/database')
```

### データベース別の接続文字列

#### SQLite（ファイルベース）

```python
# 相対パス
engine = create_engine('sqlite:///tutorial.db')

# 絶対パス
engine = create_engine('sqlite:////absolute/path/to/tutorial.db')

# インメモリ（テスト用）
engine = create_engine('sqlite:///:memory:')
```

#### PostgreSQL

```python
# psycopg2ドライバ（推奨）
engine = create_engine('postgresql+psycopg2://user:password@localhost:5432/mydb')

# asyncpg（非同期）
engine = create_engine('postgresql+asyncpg://user:password@localhost:5432/mydb')
```

#### MySQL

```python
# PyMySQL
engine = create_engine('mysql+pymysql://user:password@localhost:3306/mydb')

# mysqlclient
engine = create_engine('mysql+mysqldb://user:password@localhost:3306/mydb')
```

## コネクションプール

### コネクションプールとは

データベース接続を事前に作成し、再利用可能な状態でプールに保管する仕組みです。

```
リクエスト1
    │
    ▼
┌─────────────────┐     接続を借りる      ┌──────────┐
│ アプリケーション │ ───────────────────► │   Pool   │
│                 │                      │ ┌──┐┌──┐ │
│                 │ ◄─────────────────── │ │  ││  │ │
└─────────────────┘     接続を返す       │ └──┘└──┘ │
    │                                    └──────────┘
    │ クエリ実行
    │
    ▼
┌─────────────────┐
│ データベース    │
└─────────────────┘
```

### なぜコネクションプールが必要か？

#### ❌ プールなしの場合

```python
# リクエストごとに接続を作成・破棄
for _ in range(100):
    conn = create_connection()  # 遅い！
    conn.execute("SELECT ...")
    conn.close()                # 遅い！
```

**問題点**:
- 接続確立のオーバーヘッド（TCP handshake、認証等）
- リソースの無駄（頻繁な作成・破棄）
- データベースへの負荷

#### ✅ プールありの場合

```python
# 事前に作成した接続を再利用
for _ in range(100):
    conn = pool.get_connection()  # 高速！
    conn.execute("SELECT ...")
    pool.return_connection(conn)  # 高速！
```

**メリット**:
- 接続確立のコストを削減
- リソースの効率的な利用
- スループットの向上

### プールの設定

```python
from sqlalchemy import create_engine

engine = create_engine(
    'sqlite:///tutorial.db',

    # プールサイズ（同時接続数）
    pool_size=5,

    # 最大オーバーフロー（一時的に増やせる数）
    max_overflow=10,

    # プール内の接続の再利用回数制限
    pool_recycle=3600,

    # 接続のタイムアウト（秒）
    pool_timeout=30,

    # プール取得前の接続チェック
    pool_pre_ping=True,

    # ログ出力（開発時）
    echo=True
)
```

### プールの動作原理

```
初期状態（pool_size=3）
┌─────────────────┐
│  Available      │
│  ┌──┐┌──┐┌──┐  │
│  │C1││C2││C3│  │
│  └──┘└──┘└──┘  │
└─────────────────┘
│  In Use         │
│  (empty)        │
└─────────────────┘

リクエスト1が接続を取得
┌─────────────────┐
│  Available      │
│  ┌──┐┌──┐       │
│  │C2││C3│       │
│  └──┘└──┘       │
└─────────────────┘
│  In Use         │
│  ┌──┐           │
│  │C1│ ← リクエスト1
│  └──┘           │
└─────────────────┘

リクエスト2, 3, 4が接続を取得
┌─────────────────┐
│  Available      │
│  (empty)        │
└─────────────────┘
│  In Use         │
│  ┌──┐┌──┐┌──┐  │
│  │C1││C2││C3│  │
│  └──┘└──┘└──┘  │
└─────────────────┘

リクエスト5（プール枯渇！）
max_overflow=2の場合
┌─────────────────┐
│  Available      │
│  (empty)        │
└─────────────────┘
│  In Use         │
│  ┌──┐┌──┐┌──┐  │
│  │C1││C2││C3│  │
│  └──┘└──┘└──┘  │
│  ┌──┐┌──┐      │ ← Overflow接続
│  │C4││C5│      │
│  └──┘└──┘      │
└─────────────────┘
```

## 実践ハンズオン

### 1. 基本的な接続

このコードを `01_basic_connection.py` に書いて実行してみましょう。

```python
from sqlalchemy import create_engine, text

# Engineの作成
engine = create_engine('sqlite:///tutorial.db', echo=True)

# 接続とクエリ実行
with engine.connect() as conn:
    result = conn.execute(text("SELECT 'Hello SQLAlchemy!' as message"))
    print(result.fetchone())
```

### 2. トランザクション

```python
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///tutorial.db')

# 自動コミット
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    conn.commit()  # 明示的なコミット

# begin()を使うと自動的にコミット
with engine.begin() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER)"))
    conn.execute(text("INSERT INTO test VALUES (1)"))
    # ブロックを抜けると自動的にコミット
```

### 3. プールの動作確認

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'sqlite:///tutorial.db',
    poolclass=QueuePool,
    pool_size=2,
    max_overflow=3,
    echo_pool=True  # プールのログを表示
)

# 複数の接続を同時に取得
connections = []
for i in range(5):
    conn = engine.connect()
    connections.append(conn)
    print(f"接続{i+1}を取得")

# 接続を返却
for i, conn in enumerate(connections):
    conn.close()
    print(f"接続{i+1}を返却")
```

## Engineのベストプラクティス

### 1. Engineはシングルトンで

```python
# ❌ 悪い例: リクエストごとにEngine作成
def handle_request():
    engine = create_engine('sqlite:///db.db')  # NG!
    # ...

# ✅ 良い例: アプリケーション起動時に1回だけ作成
# config.py
engine = create_engine('sqlite:///db.db')

# main.py
from config import engine

def handle_request():
    with engine.connect() as conn:
        # ...
```

### 2. echoは開発時のみ

```python
import os

engine = create_engine(
    'sqlite:///db.db',
    echo=os.getenv('ENV') == 'development'
)
```

### 3. pool_pre_pingで接続チェック

```python
# 長時間アイドル状態の接続を自動的にチェック
engine = create_engine(
    'postgresql://...',
    pool_pre_ping=True  # 接続前にSELECT 1を実行
)
```

## まとめ

- **Engine**はデータベース接続の中核コンポーネント
- **コネクションプール**で接続を効率的に再利用
- Engineは**アプリケーション全体で1つ**作成
- `pool_size`、`max_overflow`で同時接続数を制御
- `echo=True`で発行されるSQLを確認可能

次の章では、ORMを使ったモデル定義について学びます。
