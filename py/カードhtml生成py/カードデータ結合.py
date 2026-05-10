import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import re

def extract_number(filepath):
    """パスの最初の数字部分を抽出して数値として返す"""
    match = re.search(r'(\d+)', filepath)
    return int(match.group(1)) if match else 9999

def run_combine():
    # 1. フォルダを選択
    input_dir = filedialog.askdirectory(title="JSONフォルダ(a1など)を選択")
    if not input_dir: return

    # 2. 保存パスを html/pkpk/data/cards に変更
    folder_name = os.path.basename(input_dir)    # 'a1'
    output_filename = f"{folder_name}-all-cards.json"
    
    # pyフォルダの一つ上の階層の data/cards に出力
    script_dir = os.path.dirname(os.path.abspath(__file__))  # /html/pkpk/py/カードデータ結合py
    parent_dir = os.path.dirname(script_dir)                 # /html/pkpk/py
    grandparent_dir = os.path.dirname(parent_dir)            # /html/pkpk
    
    output_dir = os.path.join(grandparent_dir, "data", "cards")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    raw_data_list = []

    try:
        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                if filename.endswith('.json') and filename not in ['index.json', 'all-cards.json', output_filename]:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        rel_path = os.path.relpath(file_path, input_dir).replace('\\', '/')
                        data['_relative_path'] = rel_path
                        raw_data_list.append(data)

        raw_data_list.sort(key=lambda x: extract_number(x['_relative_path']))

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data_list, f, ensure_ascii=False, separators=(',', ':'))

        messagebox.showinfo("完了", f"保存先: {output_path}\n{len(raw_data_list)}枚を結合しました！")

    except Exception as e:
        messagebox.showerror("エラー", str(e))

# GUI
root = tk.Tk()
root.title("JSON自動結合")
btn = tk.Button(root, text="フォルダを選択して結合", command=run_combine)
btn.pack(padx=50, pady=50)
root.mainloop()
