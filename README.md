# SQLAlchemy ハンズオンチュートリアル

Pythonの最も人気のあるORMライブラリ、SQLAlchemyを体系的に学ぶための包括的なチュートリアルです。

## 特徴

- **詳細な技術解説**: 各機能の技術的原理をテキスト図解を含めて詳しく説明
- **段階的な学習**: 基礎から応用まで7つの章で体系的に学習
- **実践的なハンズオン**: 各章に実行可能なコード例を用意
- **自動実行システム**: ファイルを編集・保存すると自動的に実行される開発環境
- **Alembic統合**: データベースマイグレーション管理も含む

## 📚 チュートリアル構成

### [第1章: SQLAlchemy入門](./tutorials/chapter01/README.md)
- SQLAlchemyとは何か
- ORMとCoreの違い
- アーキテクチャと技術的原理
- Identity Map、Unit of Work、Lazy Loadingの仕組み

### [第2章: データベース接続とエンジン](./tutorials/chapter02/README.md)
- Engineの役割と動作原理
- コネクションプールの詳細な仕組み
- 各種データベースへの接続方法
- ベストプラクティス

### [第3章: モデル定義とテーブルマッピング](./tutorials/chapter03/README.md)
- DeclarativeBaseによるモデル定義
- Mapped型とmapped_columnの使い方
- カラムの型とオプション
- テーブル作成の内部動作

### [第4章: CRUD操作とセッション管理](./tutorials/chapter04/README.md)
- Sessionの役割と重要性
- Create、Read、Update、Deleteの実装
- トランザクション管理
- セッションのライフサイクル

### [第5章: リレーションシップとJOIN](./tutorials/chapter05/README.md)
- 1対多、多対多リレーションシップ
- 外部キー制約の動作
- Lazy Loading vs Eager Loading
- N+1問題の解決

### [第6章: 高度なクエリとCore API](./tutorials/chapter06/README.md)
- 複雑なフィルタリング
- 集約関数とグループ化
- サブクエリの活用
- SQLAlchemy Core APIの使い方

### [第7章: Alembicによるマイグレーション](./tutorials/chapter07/README.md)
- マイグレーションの必要性
- Alembicの基本操作
- スキーマ変更の管理
- 本番環境での適用戦略

## 🚀 クイックスタート

### 1. 環境構築

```bash
# リポジトリのクローン
git clone <repository-url>
cd sql-alchemy-demo

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. チュートリアルの進め方

#### 方法A: 自動実行モード（推奨）

ファイルを編集・保存すると自動的に実行されます。

```bash
# 自動実行モードを起動
python utils/auto_runner.py tutorials/chapter02

# 別のターミナルで
# tutorials/chapter02/01_basic_connection.py を編集・保存
# → 自動的に実行される！
```

#### 方法B: 手動実行

```bash
# 各章のサンプルコードを直接実行
python tutorials/chapter02/01_basic_connection.py
python tutorials/chapter03/01_basic_model.py
```

### 3. 学習の進め方

1. 各章のREADME.mdを読む
2. 技術的な原理を図解で理解する
3. ハンズオン用のPythonファイルを編集して試す
4. 自動実行で即座に結果を確認
5. 次の章へ進む

## 📁 プロジェクト構造

```
sql-alchemy-demo/
├── README.md                    # このファイル
├── requirements.txt             # 依存関係
├── .gitignore
│
├── tutorials/                   # チュートリアル
│   ├── chapter01/              # 第1章: 入門
│   │   └── README.md
│   ├── chapter02/              # 第2章: Engine
│   │   ├── README.md
│   │   └── 01_basic_connection.py
│   ├── chapter03/              # 第3章: モデル定義
│   │   ├── README.md
│   │   └── 01_basic_model.py
│   ├── chapter04/              # 第4章: CRUD
│   │   └── README.md
│   ├── chapter05/              # 第5章: リレーションシップ
│   │   └── README.md
│   ├── chapter06/              # 第6章: 高度なクエリ
│   │   └── README.md
│   └── chapter07/              # 第7章: Alembic
│       └── README.md
│
├── utils/                       # ユーティリティ
│   ├── __init__.py
│   └── auto_runner.py          # 自動実行システム
│
└── examples/                    # 追加のサンプルコード
```

## 💡 自動実行システム

このチュートリアルには、学習を効率化するための自動実行システムが含まれています。

### 使い方

```bash
# tutorialsディレクトリ全体を監視
python utils/auto_runner.py tutorials

# 特定の章だけを監視
python utils/auto_runner.py tutorials/chapter02
```

### 動作

1. 指定したディレクトリ内のPythonファイルを監視
2. ファイルが編集・保存されると自動的に検知
3. 即座にそのファイルを実行
4. 結果をターミナルに表示

### メリット

- コードを書いたら即座に結果を確認
- 試行錯誤が高速化
- ハンズオン学習に最適

## 🔧 必要な環境

- Python 3.11以上
- SQLite（Python標準ライブラリに含まれる）
- PostgreSQL（オプション、第2章で解説）

## 📦 インストールされるパッケージ

- **sqlalchemy** (2.0+): ORM/Core API
- **alembic**: データベースマイグレーション
- **watchdog**: ファイル監視（自動実行用）
- **ipython**: 対話的シェル
- **pytest**: テスト
- **black**: コードフォーマッター
- **psycopg2-binary**: PostgreSQLドライバ（オプション）

## 📖 推奨学習順序

### 初心者向け
1. 第1章で全体像を把握
2. 第2章でデータベース接続を理解
3. 第3章でモデル定義を学ぶ
4. 第4章でCRUDを習得
5. 第7章でAlembicを学ぶ

### 経験者向け
1. 第1章を軽く読む（原理の理解）
2. 第5章でリレーションシップを学ぶ
3. 第6章で高度なクエリを習得
4. 第7章でAlembicをマスター

## 🎯 学習目標

このチュートリアルを完了すると、以下のことができるようになります:

- [ ] SQLAlchemyの基本概念と技術的原理を理解する
- [ ] データベース接続とエンジンを適切に管理できる
- [ ] ORMモデルを定義してテーブルを作成できる
- [ ] CRUD操作を実装できる
- [ ] リレーションシップを設計・実装できる
- [ ] N+1問題を理解し回避できる
- [ ] 複雑なクエリを構築できる
- [ ] Alembicでスキーマ変更を管理できる

## 🌟 特徴的な内容

### 詳細な技術解説

各機能について、表面的な使い方だけでなく、内部でどのように動作しているかを詳しく解説しています。

例:
- Identity Mapの仕組み
- Unit of Workパターン
- コネクションプールの動作原理
- Lazy Loadingの実装

### テキスト図解

複雑な概念を視覚的に理解できるよう、ASCIIアートによる図解を豊富に用意しています。

```
Session (アイデンティティマップ)
┌─────────────────────────────────┐
│  Key      │  Object              │
│──────────────────────────────────│
│ User:1    │  <User id=1>         │
│ User:2    │  <User id=2>         │
└─────────────────────────────────┘
```

## 🤝 コントリビューション

改善提案やバグ報告は大歓迎です！

## 📝 ライセンス

MIT License

## 🔗 参考リンク

- [SQLAlchemy公式ドキュメント](https://docs.sqlalchemy.org/)
- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0チュートリアル](https://docs.sqlalchemy.org/en/20/tutorial/)

## 📮 フィードバック

このチュートリアルに関するフィードバックや質問があれば、Issueを作成してください。

---

**Happy Learning! 🎉**

SQLAlchemyの世界を楽しんでください！
