import os
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, Radiobutton, IntVar

def natural_sort_key(s):
    """
    文字列内の数値部分を数値として扱う自然順ソート用のキーを生成
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def find_files(start_path, file_extension):
    """指定されたパス以下の特定の拡張子のファイルを再帰的に探し、相対パスのリストを返す"""
    files_list = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.lower().endswith(file_extension):
                rel_path = os.path.relpath(os.path.join(root, file), start_path)
                # Windowsの場合はパス区切りをスラッシュに統一
                rel_path = rel_path.replace('\\', '/')
                files_list.append(rel_path)
    
    # 自然順ソートで並び替え
    return sorted(files_list, key=natural_sort_key)

def select_folder():
    """フォルダ選択ダイアログを開き、選択された拡張子のファイルを検索"""
    folder_selected = filedialog.askdirectory(title="検索するフォルダを選択")
    if folder_selected:
        try:
            # 選択された拡張子を取得
            extension = '.json' if file_type.get() == 1 else '.webp'
            
            files_list = find_files(folder_selected, extension)
            
            if files_list:
                save_file(files_list, folder_selected, extension)
            else:
                messagebox.showinfo("情報", f"選択したフォルダ内に{extension}ファイルが見つかりませんでした。")
        except Exception as e:
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")

def save_file(files_list, source_folder, extension):
    """結果を保存するファイルを選択し、JSONファイルに書き出す"""
    file_path = filedialog.asksaveasfilename(
        title="結果を保存",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(files_list, f, indent=4, ensure_ascii=False)
            
            # 拡張子に応じたメッセージ
            file_type_str = "JSON" if extension == '.json' else "WebP"
            messagebox.showinfo("完了", 
                f"ファイルを保存しました:\n{file_path}\n\n"
                f"検索元フォルダ: {source_folder}\n"
                f"見つかった{file_type_str}ファイル数: {len(files_list)}")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました: {e}")

def main():
    """メインウィンドウを作成"""
    global file_type
    root = tk.Tk()
    root.title("ファイルパス収集ツール")
    root.geometry("400x250")

    # 説明ラベル
    label = tk.Label(root, text="検索するファイルの種類を選択してください", font=("Arial", 12))
    label.pack(pady=20)

    # ラジオボタンの変数（1: JSON, 2: WebP）
    file_type = IntVar(value=1)  # デフォルトはJSON

    # ラジオボタンフレーム
    radio_frame = tk.Frame(root)
    radio_frame.pack(pady=10)

    # JSONラジオボタン
    json_radio = Radiobutton(radio_frame, text="JSONファイル (.json)", 
                             variable=file_type, value=1, font=("Arial", 11))
    json_radio.pack(anchor=tk.W, pady=5)

    # WebPラジオボタン
    webp_radio = Radiobutton(radio_frame, text="WebPファイル (.webp)", 
                             variable=file_type, value=2, font=("Arial", 11))
    webp_radio.pack(anchor=tk.W, pady=5)

    # 検索ボタン
    select_button = tk.Button(root, text="フォルダを選択して検索", 
                             command=select_folder, font=("Arial", 12), 
                             width=20, height=2)
    select_button.pack(pady=10)

    # 終了ボタン
    exit_button = tk.Button(root, text="終了", command=root.quit, 
                           font=("Arial", 10), width=10)
    exit_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()