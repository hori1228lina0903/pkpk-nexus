import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

class JsonCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSONファイル一括コピーツール")
        self.root.geometry("650x280")
        self.root.resizable(True, True)

        # 変数
        self.source_dir = ""
        self.dest_dir = ""

        # GUI要素の作成
        self.create_widgets()

    def create_widgets(self):
        # フレーム1: コピー元選択
        frame_source = tk.LabelFrame(self.root, text="コピー元フォルダ", padx=5, pady=5)
        frame_source.pack(fill="x", padx=10, pady=5)

        self.source_label = tk.Label(frame_source, text="未選択", anchor="w", bg="lightgray")
        self.source_label.pack(fill="x", side="left", expand=True, padx=(0, 5))

        btn_source = tk.Button(frame_source, text="参照", command=self.select_source)
        btn_source.pack(side="right")

        # フレーム2: 出力先選択
        frame_dest = tk.LabelFrame(self.root, text="出力先フォルダ", padx=5, pady=5)
        frame_dest.pack(fill="x", padx=10, pady=5)

        self.dest_label = tk.Label(frame_dest, text="未選択", anchor="w", bg="lightgray")
        self.dest_label.pack(fill="x", side="left", expand=True, padx=(0, 5))

        btn_dest = tk.Button(frame_dest, text="参照", command=self.select_dest)
        btn_dest.pack(side="right")

        # フレーム3: ボタンエリア
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=15)

        # コピー専用ボタン
        self.copy_btn = tk.Button(
            frame_buttons, 
            text="📁 コピーのみ", 
            command=lambda: self.start_copy(delete_original=False),
            width=15,
            height=2,
            bg="lightblue",
            font=("", 10, "bold")
        )
        self.copy_btn.pack(side="left", padx=10)

        # コピー＆削除ボタン
        self.copy_delete_btn = tk.Button(
            frame_buttons, 
            text="⚠️ コピー＆削除", 
            command=lambda: self.start_copy(delete_original=True),
            width=15,
            height=2,
            bg="salmon",
            font=("", 10, "bold")
        )
        self.copy_delete_btn.pack(side="left", padx=10)

        # プログレスバー
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill="x", padx=10, pady=10)

        # ステータス表示
        self.status_label = tk.Label(self.root, text="", fg="blue")
        self.status_label.pack()

    def select_source(self):
        folder = filedialog.askdirectory(title="コピー元フォルダを選択")
        if folder:
            self.source_dir = folder
            self.source_label.config(text=folder)
            self.check_ready()

    def select_dest(self):
        folder = filedialog.askdirectory(title="出力先フォルダを選択")
        if folder:
            self.dest_dir = folder
            self.dest_label.config(text=folder)
            self.check_ready()

    def check_ready(self):
        if self.source_dir and self.dest_dir:
            self.copy_btn.config(state="normal")
            self.copy_delete_btn.config(state="normal")
        else:
            self.copy_btn.config(state="disabled")
            self.copy_delete_btn.config(state="disabled")

    def start_copy(self, delete_original=False):
        if not self.source_dir or not self.dest_dir:
            messagebox.showwarning("警告", "コピー元と出力先の両方を選択してください。")
            return

        # コピー元と出力先が同じ場合はエラー
        if os.path.samefile(self.source_dir, self.dest_dir):
            messagebox.showerror("エラー", "コピー元と出力先が同じフォルダです。別のフォルダを指定してください。")
            return

        # ボタンに応じた確認メッセージ
        if delete_original:
            msg = (
                f"【警告】コピー＆削除モード\n\n"
                f"コピー元:\n{self.source_dir}\n\n"
                f"出力先:\n{self.dest_dir}\n\n"
                f"⚠️ 以下の処理が実行されます ⚠️\n"
                f"1. JSONファイルを出力先にコピー\n"
                f"2. コピー成功した元のJSONファイルを削除\n\n"
                f"この操作は元に戻せません！\n\n"
                f"続行しますか？"
            )
            title = "⚠️ 確認 - コピー＆削除モード ⚠️"
        else:
            msg = (
                f"コピーのみモード\n\n"
                f"コピー元:\n{self.source_dir}\n\n"
                f"出力先:\n{self.dest_dir}\n\n"
                f"この設定でコピーを開始しますか？"
            )
            title = "確認 - コピーのみ"

        if not messagebox.askyesno(title, msg):
            return

        # 別スレッドで処理
        if delete_original:
            self.copy_delete_btn.config(state="disabled", text="処理中...")
        else:
            self.copy_btn.config(state="disabled", text="処理中...")

        self.progress.start()
        self.status_label.config(text="処理を実行中...")

        thread = threading.Thread(target=self.process_files, args=(delete_original,))
        thread.daemon = True
        thread.start()

    def process_files(self, delete_original):
        try:
            copied_files = []  # コピー成功したファイルのパス
            failed_copies = []

            source_root = os.path.abspath(self.source_dir)
            dest_root = os.path.abspath(self.dest_dir)

            # JSONファイル一覧を取得
            all_json_files = []
            for current_dir, subdirs, files in os.walk(source_root):
                for file in files:
                    if file.lower().endswith('.json'):
                        full_path = os.path.join(current_dir, file)
                        all_json_files.append(full_path)

            total_files = len(all_json_files)
            if total_files == 0:
                self.update_status("JSONファイルが見つかりませんでした。")
                self.progress.stop()
                messagebox.showinfo("情報", "コピー元フォルダ内にJSONファイルは見つかりませんでした。")
                self.reset_buttons()
                return

            processed = 0
            for full_path in all_json_files:
                rel_path = os.path.relpath(full_path, source_root)
                dest_path = os.path.join(dest_root, rel_path)

                try:
                    # 出力先ディレクトリ作成
                    dest_dir = os.path.dirname(dest_path)
                    os.makedirs(dest_dir, exist_ok=True)

                    # コピー実行
                    shutil.copy2(full_path, dest_path)
                    copied_files.append(full_path)
                    processed += 1

                    if processed % 10 == 0:
                        self.update_status(f"処理中... {processed}/{total_files} 完了")

                except Exception as e:
                    failed_copies.append((full_path, str(e)))
                    processed += 1

            # コピー結果
            copy_success = len(copied_files)
            copy_failed = len(failed_copies)

            # 削除処理（モードによる）
            deleted_count = 0
            delete_errors = []

            if delete_original and copy_success > 0:
                self.update_status(f"コピー完了。元ファイルを削除中...")
                for file_path in copied_files:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        delete_errors.append((file_path, str(e)))

            # 結果表示
            self.progress.stop()

            # 結果メッセージ作成
            if delete_original:
                mode_name = "コピー＆削除"
            else:
                mode_name = "コピーのみ"

            result_msg = f"【{mode_name}】\n\n"
            result_msg += f"✅ コピー成功: {copy_success} 個\n"
            if copy_failed > 0:
                result_msg += f"❌ コピー失敗: {copy_failed} 個\n"

            if delete_original:
                result_msg += f"🗑️ 削除した元ファイル: {deleted_count} 個\n"
                if delete_errors:
                    result_msg += f"⚠️ 削除失敗: {len(delete_errors)} 個\n"

            result_msg += f"\n出力先: {self.dest_dir}"

            self.update_status(f"完了！ {copy_success}個のJSONファイルを処理しました。")

            # エラーがあった場合の処理
            if copy_failed > 0 or delete_errors:
                log_path = os.path.join(self.dest_dir, "_copy_errors.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"=== {mode_name} モード エラーログ ===\n\n")
                    if copy_failed > 0:
                        f.write("【コピーエラー】\n")
                        for path, err in failed_copies:
                            f.write(f"  ファイル: {path}\n")
                            f.write(f"  エラー: {err}\n\n")
                    if delete_errors:
                        f.write("【削除エラー】\n")
                        for path, err in delete_errors:
                            f.write(f"  ファイル: {path}\n")
                            f.write(f"  エラー: {err}\n\n")
                messagebox.showwarning(
                    "処理完了（一部エラー）", 
                    f"{result_msg}\n\nエラー詳細はログファイルを確認してください。\n\nログ: {log_path}"
                )
            else:
                messagebox.showinfo("完了", result_msg)

        except Exception as e:
            self.progress.stop()
            self.update_status(f"エラー発生: {str(e)}")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")
        finally:
            self.reset_buttons()

    def reset_buttons(self):
        """ボタンを元の状態に戻す"""
        def reset():
            self.copy_btn.config(state="normal", text="📁 コピーのみ")
            self.copy_delete_btn.config(state="normal", text="⚠️ コピー＆削除")
            self.progress.stop()
        self.root.after(0, reset)

    def update_status(self, message):
        def update():
            self.status_label.config(text=message)
        self.root.after(0, update)


if __name__ == "__main__":
    root = tk.Tk()
    app = JsonCopyApp(root)
    root.mainloop()