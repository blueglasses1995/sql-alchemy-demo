# 第13章: カスタム型とComposite Types

SQLAlchemyでカスタムデータ型を定義し、複合型（Composite Types）を使用する方法を学びます。

## TypeDecorator

既存の型をラップしてカスタム動作を追加します。

```python
from sqlalchemy import TypeDecorator, String
import json

class JSONEncodedDict(TypeDecorator):
    """辞書をJSON文字列として保存"""
    impl = String

    def process_bind_param(self, value, dialect):
        """Pythonオブジェクト → DB"""
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        """DB → Pythonオブジェクト"""
        if value is not None:
            return json.loads(value)
        return None

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    settings: Mapped[dict] = mapped_column(JSONEncodedDict(1000))

# 使用例
user.settings = {"theme": "dark", "language": "ja"}
# DBには '{"theme":"dark","language":"ja"}' として保存
```

## Composite Types

複数のカラムを1つのPythonオブジェクトとして扱います。

```python
from sqlalchemy.orm import composite

class Point:
    """座標を表すクラス"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __composite_values__(self):
        return self.x, self.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class Vertex(Base):
    __tablename__ = 'vertices'
    id: Mapped[int] = mapped_column(primary_key=True)
    x: Mapped[int]
    y: Mapped[int]

    # Composite
    point = composite(Point, x, y)

# 使用例
vertex = Vertex()
vertex.point = Point(10, 20)
print(vertex.x, vertex.y)  # 10, 20
```

詳細な実装例は公式ドキュメントを参照してください。
