import os
import json
import tkinter as tk
from tkinter import filedialog

# パック情報の定義 (セット名とトータル枚数)
PACK_CONFIG = {
    # Aシリーズ
    "a1": {"set": "Genetic Apex", "total": 286},
    "a1a": {"set": "Mythical Island", "total": 86},
    "a2": {"set": "Space-Time Smackdown", "total": 207},
    "a2a": {"set": "Triumphant Light", "total": 96},
    "a2b": {"set": "Shining Revelry", "total": 111},
    "a3": {"set": "Celestial Guardians", "total": 239},
    "a3a": {"set": "Extradimensional Crisis", "total": 103},
    "a3b": {"set": "Eevee Grove", "total": 107},
    "a4": {"set": "Wisdom of Sea and Sky", "total": 241},
    "a4a": {"set": "Secluded Springs", "total": 105},
    "a4b": {"set": "Deluxe Pack ex", "total": 379},
    # Bシリーズ
    "b1": {"set": "Mega Rising", "total": 331},
    "b1a": {"set": "Crimson Blaze", "total": 103},
    "b2": {"set": "Fantastical Parade", "total": 234},
    "b2a": {"set": "Paldean Wonders", "total": 131},
    "b2b": {"set": "Mega Shine", "total": 117},
    # プロモ
    "promo-a": {"set": "Promo A", "total": 117},
    "promo-b": {"set": "Promo B", "total": 48},
}

def check_and_export_json():
    # 1. GUIでフォルダを選択
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    target_dir = filedialog.askdirectory(title="パック名（a1, b1等）のフォルダを選択してください")
    root.destroy()

    if not target_dir:
        print("フォルダが選択されなかったため、終了します。")
        return

    # 2. フォルダ名からパックキーを判定
    # パスからフォルダ名（例: "a3a"）のみを取得し、小文字にして判定
    folder_name = os.path.basename(target_dir).lower()
    
    if folder_name not in PACK_CONFIG:
        print(f"❌ エラー: フォルダ名 '{folder_name}' に対応するパック設定が見つかりません。")
        print(f"対応フォルダ名: {', '.join(PACK_CONFIG.keys())}")
        input("\nEnterキーを押して終了...")
        return

    config = PACK_CONFIG[folder_name]
    start = 1
    end = config["total"]
    set_name = config["set"]

    # 3. フォルダ内の数字フォルダをチェック
    existing_nums = []
    for name in os.listdir(target_dir):
        if os.path.isdir(os.path.join(target_dir, name)):
            try:
                existing_nums.append(int(name))
            except ValueError:
                continue
    
    existing_set = set(existing_nums)
    expected_set = set(range(start, end + 1))

    # 4. 欠損番号の抽出
    missing_nums = sorted(list(expected_set - existing_set))

    # 5. JSONデータの作成
    result_data = {
        "pack_key": folder_name,
        "set_name": set_name,
        "check_range": {"start": start, "end": end},
        "missing_count": len(missing_nums),
        "missing_numbers": missing_nums
    }

    # 6. JSONを保存
    output_file = os.path.join(target_dir, f"missing_{folder_name}.json")
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*40)
        print(f"✅ フォルダ名 '{folder_name}' を自動認識しました")
        print(f"セット名: {set_name}")
        print(f"調査範囲: {start} ～ {end}")
        print(f"欠損数  : {len(missing_nums)} 件")
        print(f"結果保存: {output_file}")
        print("="*40)
        
    except Exception as e:
        print(f"ファイルの保存中にエラーが発生しました: {e}")
        
try:
    input("\nEnterキーを押すと終了します...")
except EOFError:
    pass
    
if __name__ == "__main__":
    check_and_export_json()
