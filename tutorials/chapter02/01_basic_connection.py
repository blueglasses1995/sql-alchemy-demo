"""
第2章 ハンズオン1: 基本的なデータベース接続

このファイルを編集・保存すると自動的に実行されます。
"""

from sqlalchemy import create_engine, text

print("=" * 60)
print("SQLAlchemy 基本的な接続のデモ")
print("=" * 60)

# Engineの作成
# echo=True にすると、実行されるSQLが表示されます
engine = create_engine('sqlite:///tutorial.db', echo=True)

print("\n✅ Engineを作成しました")
print(f"   データベース: tutorial.db")
print(f"   方言: {engine.dialect.name}")
print(f"   ドライバー: {engine.driver}")

# 接続してクエリを実行
print("\n📡 データベースに接続してクエリを実行...")

with engine.connect() as conn:
    # シンプルなSELECT文
    result = conn.execute(text("SELECT 'Hello SQLAlchemy!' as message"))
    row = result.fetchone()

    print(f"\n🎉 クエリ結果: {row.message}")

    # SQLiteのバージョンを確認
    result = conn.execute(text("SELECT sqlite_version() as version"))
    row = result.fetchone()
    print(f"📦 SQLiteバージョン: {row.version}")

print("\n" + "=" * 60)
print("✨ 実行完了！")
print("=" * 60)
