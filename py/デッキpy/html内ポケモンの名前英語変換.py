import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

def translate_assets():
    # 翻訳マップ
    translation_map = {
        "スイクンex": "Suicune ex",
        "サザンドラ": "Hydreigon",
        "メガチルタリス": "Mega Altaria",
        "ジバコイル(紅蓮)": "Magnezone (Crimson)",
        "ミミッキュex": "Mimikyu ex",
        "ギラティナex": "Giratina ex",
        "メガカイロス": "Mega Pinsir",
        "メガリザードンY": "Mega Charizard Y",
        "ワタッコex": "Jumpluff ex",
        "シャンデラ(夢幻)": "Chandelure (Phantasm)",
        "メガバシャーモ": "Mega Blaziken",
        "オーガポンex(緑)": "Ogerpon ex (Teal Mask)",
        "メガアブソル": "Mega Absol",
        "アクジキングex": "Guzzlord ex",
        "ジュナイパーex": "Decidueye ex",
        "メガハガネール": "Mega Steelix",
        "メガチャーレム": "Mega Medicham",
        "ゲッコウガ": "Greninja",
        "メガガルーラ": "Mega Kangaskhan",
        "カビゴンex": "Snorlax ex",
        "マスキッパ": "Carnivine",
        "セレビィ": "Celebi",
        "ガラルタチフサグマ": "Galarian Obstagoon",
        "エーフィex": "Espeon ex",
        "ガチゴラス": "Tyrantrum",
        "メガミミロップ": "Mega Lopunny",
        "アローラキュウコンex": "Alolan Ninetales ex",
        "クロバットex": "Crobat ex",
        "メガサーナイト": "Mega Gardevoir",
        "サンダースex": "Jolteon ex",
        "マッシブーンex": "Buzzwole ex",
        "ボーマンダ": "Salamence"
    }

    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo("手順 1/2", "翻訳したい【HTMLファイル】を選択してください。")
    html_path = filedialog.askopenfilename(title="1. HTMLファイルを選択", filetypes=[("HTML files", "*.html")])
    if not html_path: return

    messagebox.showinfo("手順 2/2", "webp画像が保存されている【フォルダ】を選択してください。")
    img_dir = filedialog.askdirectory(title="2. webp画像フォルダを選択")
    if not img_dir: return

    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 長い名前から順に置換（部分一致による誤置換防止）
        sorted_keys = sorted(translation_map.keys(), key=len, reverse=True)

        for jp in sorted_keys:
            en = translation_map[jp]
            
            # 1. href属性内のパスを置換 (名前 + deck.html にする)
            # 例: href="/decks/スイクンex.html" -> href="/decks/Suicune ex deck.html"
            href_pattern = f'href="/decks/{jp}.html"'
            new_href = f'href="/decks/{en} deck.html"'
            html_content = html_content.replace(href_pattern, new_href)

            # 2. その他のテキスト部分を置換
            html_content = html_content.replace(jp, en)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 画像リネーム（画像ファイル名には " deck" を含めない設定）
        rename_count = 0
        for jp_name, en_name in translation_map.items():
            old_file = os.path.join(img_dir, f"{jp_name}.webp")
            new_file = os.path.join(img_dir, f"{en_name}.webp")
            if os.path.exists(old_file):
                os.rename(old_file, new_file)
                rename_count += 1

        messagebox.showinfo("完了", f"処理完了！\n作成HTML: {os.path.basename(html_path)}\nリネーム画像: {rename_count}件")

    except Exception as e:
        messagebox.showerror("エラー", f"エラーが発生しました:\n{e}")

if __name__ == "__main__":
    translate_assets()
