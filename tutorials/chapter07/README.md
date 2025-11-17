# 第7章: Alembicによるマイグレーション管理

## 学習目標
- マイグレーションの必要性を理解する
- Alembicの基本的な使い方を学ぶ
- スキーマ変更を安全に管理する方法を習得する
- 本番環境でのマイグレーション戦略を理解する

## マイグレーションとは

**マイグレーション**は、データベーススキーマの変更を管理する仕組みです。

### なぜマイグレーションが必要か？

```
開発フェーズ1
┌──────────────┐
│ users table  │
├──────────────┤
│ id           │
│ name         │
│ email        │
└──────────────┘

↓ 新しい要件

開発フェーズ2
┌──────────────┐
│ users table  │
├──────────────┤
│ id           │
│ name         │
│ email        │
│ age          │ ← 追加
│ is_active    │ ← 追加
└──────────────┘
```

**問題**:
- チームメンバー間でスキーマの同期が必要
- 本番環境への反映が複雑
- 変更履歴の管理が困難
- ロールバックが難しい

**マイグレーションによる解決**:
- スキーマ変更を履歴として管理
- チーム全体で同じ状態を保つ
- 本番環境への適用が自動化
- ロールバックが容易

## Alembicとは

Alembicは、SQLAlchemy用のデータベースマイグレーションツールです。

### Alembicのアーキテクチャ

```
┌──────────────────────────────────────┐
│ Alembic                              │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ Migration Scripts              │  │
│  │  ├ 001_initial.py              │  │
│  │  ├ 002_add_age_column.py       │  │
│  │  └ 003_add_index.py            │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ alembic.ini (設定ファイル)     │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ env.py (環境設定)              │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
                │
                ▼
        ┌──────────────┐
        │ alembic_     │
        │ version      │ ← 現在のバージョンを記録
        │ テーブル     │
        └──────────────┘
                │
                ▼
          データベース
```

## Alembicの初期化

### 1. Alembicの初期化

```bash
# プロジェクトディレクトリで実行
alembic init alembic
```

**作成されるファイル**:
```
プロジェクト/
├── alembic/
│   ├── versions/         ← マイグレーションファイル
│   ├── env.py            ← 環境設定
│   ├── script.py.mako    ← テンプレート
│   └── README
├── alembic.ini           ← 設定ファイル
└── (既存のファイル)
```

### 2. alembic.iniの設定

```ini
# alembic.ini

# データベース接続文字列
sqlalchemy.url = sqlite:///tutorial.db

# または環境変数から取得
# sqlalchemy.url =

# ログレベル
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### 3. env.pyの設定

```python
# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# モデルのメタデータをインポート
from models import Base  # ← 追加

# this is the Alembic Config object
config = context.config

# モデルのメタデータを設定
target_metadata = Base.metadata  # ← 追加

# ... (その他の設定)
```

## マイグレーションファイルの作成

### 自動生成

```bash
# モデルの変更を検出して自動生成
alembic revision --autogenerate -m "Add age column to users"
```

**生成されるファイル**:
```python
# alembic/versions/xxxx_add_age_column_to_users.py

"""Add age column to users

Revision ID: xxxx
Revises: yyyy
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'  # 前のバージョン
branch_labels = None
depends_on = None

def upgrade():
    """アップグレード処理（適用）"""
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))

def downgrade():
    """ダウングレード処理（取り消し）"""
    op.drop_column('users', 'age')
```

### 手動作成

```bash
# 空のマイグレーションファイルを作成
alembic revision -m "Custom migration"
```

## マイグレーションの適用

### 最新バージョンへアップグレード

```bash
# 最新まで適用
alembic upgrade head

# 特定のバージョンまで適用
alembic upgrade xxxx

# 1つ進める
alembic upgrade +1

# 2つ進める
alembic upgrade +2
```

### ダウングレード

```bash
# 1つ戻す
alembic downgrade -1

# 特定のバージョンまで戻す
alembic downgrade xxxx

# 初期状態に戻す
alembic downgrade base
```

### 現在の状態確認

```bash
# 現在のバージョンを表示
alembic current

# 履歴を表示
alembic history

# 詳細な履歴
alembic history --verbose
```

## マイグレーションの仕組み

### バージョン管理

```
データベースの状態遷移

base (初期状態)
  │
  ├─ 001: Initial tables
  │   └─ users, posts テーブル作成
  │
  ├─ 002: Add age column
  │   └─ users.age カラム追加
  │
  ├─ 003: Add index
  │   └─ users.email にインデックス
  │
  └─ head (最新)

alembic_version テーブル
┌─────────────┐
│ version_num │
├─────────────┤
│ 003         │ ← 現在のバージョン
└─────────────┘
```

### upgrade()とdowngrade()

```python
def upgrade():
    """
    このマイグレーションを適用する処理

    実行タイミング: alembic upgrade
    """
    op.add_column('users', sa.Column('age', sa.Integer()))

def downgrade():
    """
    このマイグレーションを取り消す処理

    実行タイミング: alembic downgrade
    """
    op.drop_column('users', 'age')
```

## マイグレーション操作の種類

### テーブル操作

```python
# テーブル作成
op.create_table(
    'users',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('name', sa.String(50)),
    sa.Column('email', sa.String(100))
)

# テーブル削除
op.drop_table('users')

# テーブル名変更
op.rename_table('users', 'accounts')
```

### カラム操作

```python
# カラム追加
op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))

# カラム削除
op.drop_column('users', 'age')

# カラム名変更
op.alter_column('users', 'name', new_column_name='username')

# カラム型変更
op.alter_column('users', 'age',
    type_=sa.String(10),
    existing_type=sa.Integer()
)
```

### インデックス操作

```python
# インデックス作成
op.create_index('ix_users_email', 'users', ['email'])

# インデックス削除
op.drop_index('ix_users_email', table_name='users')

# ユニークインデックス
op.create_index('ix_users_email', 'users', ['email'], unique=True)
```

### 外部キー操作

```python
# 外部キー追加
op.create_foreign_key(
    'fk_posts_user_id',
    'posts', 'users',
    ['user_id'], ['id']
)

# 外部キー削除
op.drop_constraint('fk_posts_user_id', 'posts', type_='foreignkey')
```

### データ操作

```python
from sqlalchemy import table, column

# テーブル定義（マイグレーション用）
users = table('users',
    column('id', sa.Integer),
    column('is_active', sa.Boolean)
)

# データ更新
op.execute(
    users.update().values(is_active=True)
)

# データ挿入
op.bulk_insert(users, [
    {'id': 1, 'is_active': True},
    {'id': 2, 'is_active': False},
])
```

## ベストプラクティス

### 1. マイグレーションは小さく保つ

```python
# ❌ 悪い例: 1つのマイグレーションで複数の変更
def upgrade():
    op.add_column('users', sa.Column('age', sa.Integer()))
    op.add_column('users', sa.Column('city', sa.String(50)))
    op.create_table('posts', ...)
    op.add_column('posts', ...)

# ✅ 良い例: 変更ごとに分割
# migration_1: users.age追加
# migration_2: users.city追加
# migration_3: postsテーブル作成
```

### 2. downgrade()を必ず実装

```python
# ✅ upgrade()とdowngrade()は対になる
def upgrade():
    op.add_column('users', sa.Column('age', sa.Integer()))

def downgrade():
    op.drop_column('users', 'age')
```

### 3. データマイグレーションに注意

```python
# ⚠️ 大量データの場合はバッチ処理
def upgrade():
    connection = op.get_bind()

    # バッチ処理（1000件ずつ）
    users = table('users', column('id'), column('email'))

    for offset in range(0, 1000000, 1000):
        connection.execute(
            users.update()
            .where(users.c.email.is_(None))
            .values(email='default@example.com')
            .limit(1000)
            .offset(offset)
        )
```

### 4. 本番環境での適用

```bash
# 1. まずドライラン（SQLを表示）
alembic upgrade head --sql

# 2. バックアップを取得
# ...

# 3. メンテナンスモードに
# ...

# 4. マイグレーション適用
alembic upgrade head

# 5. 動作確認
# ...

# 6. メンテナンスモード解除
```

## 実践ハンズオン

### 初期化から適用まで

```bash
# 1. Alembic初期化
alembic init alembic

# 2. env.pyを編集（モデルのインポート追加）
# 3. alembic.iniを編集（DB接続文字列設定）

# 4. 初回マイグレーション作成
alembic revision --autogenerate -m "Initial migration"

# 5. 適用
alembic upgrade head

# 6. モデルに変更を加える
# 例: User.age カラムを追加

# 7. マイグレーション生成
alembic revision --autogenerate -m "Add age to users"

# 8. 適用
alembic upgrade head

# 9. 確認
alembic current
alembic history
```

## まとめ

- **Alembic**でスキーマ変更を履歴管理
- `revision --autogenerate`で自動検出
- `upgrade`で適用、`downgrade`で取り消し
- 小さく分割し、必ずdowngradeを実装
- 本番適用前にドライランとバックアップ

これでSQLAlchemyとAlembicの基礎を一通り学習しました。
