"""
ファイル監視と自動実行システム

Pythonファイルの変更を検知して自動的に実行します。
ハンズオン学習を効率化するためのツールです。
"""

import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PythonFileHandler(FileSystemEventHandler):
    """Pythonファイルの変更を監視するハンドラー"""

    def __init__(self, target_pattern="*.py"):
        self.target_pattern = target_pattern
        self.last_modified = {}
        self.debounce_time = 1.0  # 1秒間のデバウンス時間

    def on_modified(self, event):
        """ファイルが変更されたときの処理"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Pythonファイル以外は無視
        if not file_path.suffix == '.py':
            return

        # __pycache__やhidden filesは無視
        if '__pycache__' in file_path.parts or file_path.name.startswith('.'):
            return

        # デバウンス処理（連続した変更イベントを無視）
        current_time = time.time()
        last_time = self.last_modified.get(file_path, 0)

        if current_time - last_time < self.debounce_time:
            return

        self.last_modified[file_path] = current_time

        # ファイル実行
        print(f"\n{'='*60}")
        print(f"📝 ファイル変更検知: {file_path.name}")
        print(f"{'='*60}")
        self.run_python_file(file_path)

    def run_python_file(self, file_path):
        """Pythonファイルを実行"""
        try:
            print(f"\n🚀 実行開始: python {file_path}\n")
            result = subprocess.run(
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 標準出力
            if result.stdout:
                print(result.stdout)

            # エラー出力
            if result.stderr:
                print("⚠️  エラー出力:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)

            # リターンコード
            if result.returncode == 0:
                print(f"\n✅ 実行成功 (終了コード: {result.returncode})")
            else:
                print(f"\n❌ 実行失敗 (終了コード: {result.returncode})")

        except subprocess.TimeoutExpired:
            print("\n⏱️  タイムアウト: 30秒以内に実行が完了しませんでした")
        except Exception as e:
            print(f"\n❌ 実行エラー: {e}")
        finally:
            print(f"{'='*60}\n")


def start_watching(directory="."):
    """ファイル監視を開始"""
    path = Path(directory).resolve()

    print("🔍 SQLAlchemy チュートリアル - 自動実行モード")
    print(f"📂 監視ディレクトリ: {path}")
    print("💡 Pythonファイルを編集・保存すると自動的に実行されます")
    print("⏸️  停止するには Ctrl+C を押してください\n")
    print(f"{'='*60}\n")

    event_handler = PythonFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  監視を停止します...")
        observer.stop()

    observer.join()
    print("👋 終了しました\n")


if __name__ == "__main__":
    # コマンドライン引数から監視ディレクトリを取得
    watch_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    start_watching(watch_dir)
