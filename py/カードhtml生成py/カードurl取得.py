import tkinter as tk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup
import json
import re

BASE_URL = "https://www.pokemon-zone.com"

def extract_links(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    links = soup.find_all("a", href=True)
    card_links = [
        BASE_URL + link["href"]
        for link in links
        if re.match(r"^/cards/[^/]+/[^/]+/[^/]+/?$", link["href"])
    ]
    return card_links

def save_to_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def select_file():
    file_path = filedialog.askopenfilename(
        title="HTMLファイルを選択",
        filetypes=[("HTML files", "*.html"), ("HTML files", "*.htm"), ("All files", "*.*")]
    )
    if not file_path:
        return
    try:
        links = extract_links(file_path)
        if not links:
            messagebox.showinfo("結果", "対象のリンクは見つかりませんでした。")
            return
        output_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="保存先を選択"
        )
        if output_path:
            save_to_json(links, output_path)
            messagebox.showinfo("完了", f"{len(links)} 件のリンクを抽出し、保存しました。")
    except Exception as e:
        messagebox.showerror("エラー", f"処理中にエラーが発生しました：\n{e}")

# GUI セットアップ
root = tk.Tk()
root.title("カードリンク抽出ツール")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

label = tk.Label(frame, text="HTMLファイルを選択して、カード個別ページのリンクを抽出してJSONで保存します")
label.pack(pady=(0, 10))

btn = tk.Button(frame, text="HTMLファイルを選択", command=select_file)
btn.pack()

root.mainloop()