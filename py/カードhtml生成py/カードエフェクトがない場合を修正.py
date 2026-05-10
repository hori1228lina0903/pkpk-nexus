import json
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox

def run_update():
    # GUIの初期化
    root = tk.Tk()
    root.withdraw()

    # 1. 「a1」フォルダなどを直接選択
    selected_dir = filedialog.askdirectory(title="調査対象のフォルダ（例: a1）を選択してください")
    if not selected_dir:
        return

    # a1の親フォルダを取得（a1#223のようなIDからパスを作る際の基準にするため）
    parent_dir = os.path.dirname(selected_dir)
    updated_count = 0

    # 2. 指定されたフォルダ内を再帰的に走査
    for root_path, _, files in os.walk(selected_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            
            current_json_path = os.path.join(root_path, filename)
            
            try:
                with open(current_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 「エフェクト効果」が空リスト [] かチェック
                # data.get("エフェクト効果") == [] は、キーが存在し、かつ中身が空の場合にTrueになります
                if data.get("エフェクト効果") == [] and data.get("Alternate Arts"):
                    
                    # Alternate Arts の一番目の ID (例: a1#223) を取得
                    target_id = data["Alternate Arts"][0].get("カード番号")
                    if not target_id:
                        continue
                    
                    # 親フォルダを基準に参照先パスを作成 (a1#223 -> parent/a1/223/)
                    target_rel_path = target_id.replace("#", "/")
                    target_folder = os.path.join(parent_dir, target_rel_path)
                    
                    # 参照先フォルダの中にある JSON を検索
                    target_files = glob.glob(os.path.join(target_folder, "*.json"))
                    
                    if target_files:
                        target_json_path = target_files[0]
                        
                        with open(target_json_path, 'r', encoding='utf-8') as tf:
                            target_data = json.load(tf)
                            source_effect = target_data.get("エフェクト効果")
                            
                            # 参照元に有効なエフェクト効果（空でないリスト等）がある場合のみコピー
                            if source_effect and len(source_effect) > 0:
                                data["エフェクト効果"] = source_effect
                                
                                # ファイルを上書き保存
                                with open(current_json_path, 'w', encoding='utf-8') as wf:
                                    json.dump(data, wf, ensure_ascii=False, indent=2)
                                
                                updated_count += 1
                                print(f"【更新成功】 {filename} <- {target_id}")

            except Exception as e:
                print(f"【エラー】 ファイル {filename} の処理中に問題が発生しました: {e}")

    # 3. 結果をポップアップ表示
    messagebox.showinfo("処理完了", f"選択フォルダ: {os.path.basename(selected_dir)}\n更新件数: {updated_count} 件")

if __name__ == "__main__":
    run_update()
