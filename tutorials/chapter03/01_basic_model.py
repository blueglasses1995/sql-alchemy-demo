"""
第3章 ハンズオン1: 基本的なモデル定義

このファイルを編集・保存すると自動的に実行されます。
"""

from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from typing import Optional

print("=" * 60)
print("モデル定義とテーブル作成のデモ")
print("=" * 60)

# ベースクラス
class Base(DeclarativeBase):
    pass

# Userモデル
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

print("\n✅ Userモデルを定義しました")
print(f"   テーブル名: {User.__tablename__}")
print(f"   カラム:")
for column in User.__table__.columns:
    print(f"     - {column.name}: {column.type}")

# エンジン作成
engine = create_engine('sqlite:///tutorial.db', echo=True)

print("\n📊 テーブルを作成します...")
Base.metadata.create_all(engine)

print("\n" + "=" * 60)
print("✨ テーブルの作成が完了しました！")
print("   tutorial.db ファイルを確認してください")
print("=" * 60)
