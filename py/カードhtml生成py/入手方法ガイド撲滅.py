import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import re
import datetime

def select_json_file():
    """JSONファイル選択ダイアログを表示し、選択されたファイルのパスを返す"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="パス一覧のJSONファイルを選択してください",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()
        
        return file_path
    except Exception as e:
        print(f"ファイル選択ダイアログでエラーが発生しました: {e}")
        return None

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"JSONファイルの読み込みに失敗しました: {e}")
        return None

def convert_guide_to_event(card_data):
    """
    カードデータの入手方法にある「ガイド:」を「イベント:」に変換
    「Event」が含まれる場合のみ変換
    """
    modified = False
    
    if "入手方法" in card_data and isinstance(card_data["入手方法"], list):
        new_methods = []
        for method in card_data["入手方法"]:
            if isinstance(method, str) and "ガイド:" in method:
                # 「Event」が含まれるかチェック
                if "Event" in method or "event" in method:
                    # 「ガイド:」を「イベント:」に置換
                    new_method = method.replace("ガイド:", "イベント:", 1)
                    new_methods.append(new_method)
                    modified = True
                    print(f"    ✓ 変換: {method} → {new_method}")
                else:
                    new_methods.append(method)
            else:
                new_methods.append(method)
        
        if modified:
            card_data["入手方法"] = new_methods
    
    return card_data, modified

def process_card_files(path_list, base_dir=None):
    """
    パス一覧の各JSONファイルを処理
    base_dirが指定されている場合は、相対パスとして結合
    """
    results = {
        "processed": [],
        "modified": [],
        "errors": []
    }
    
    for i, path in enumerate(path_list, 1):
        print(f"\n[{i}/{len(path_list)}] 処理中: {path}")
        
        # 実際のファイルパスを構築
        if base_dir and not os.path.isabs(path):
            full_path = os.path.join(base_dir, path)
        else:
            full_path = path
        
        # ファイルが存在するか確認
        if not os.path.exists(full_path):
            print(f"  ❌ ファイルが存在しません: {full_path}")
            results["errors"].append({"path": path, "error": "ファイルが存在しません"})
            continue
        
        try:
            # JSONファイルを読み込み
            with open(full_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            # 変換処理
            modified_data, was_modified = convert_guide_to_event(card_data)
            
            results["processed"].append(path)
            
            if was_modified:
                # 変換されたファイルを保存
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(modified_data, f, ensure_ascii=False, indent=2)
                
                results["modified"].append(path)
                print(f"  ✅ 変換して保存しました")
            else:
                print(f"  ℹ️ 変換対象の「ガイド:」はありませんでした")
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSONデコードエラー: {e}")
            results["errors"].append({"path": path, "error": f"JSONデコードエラー: {e}"})
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            results["errors"].append({"path": path, "error": str(e)})
    
    return results

def save_report(results, output_file):
    """処理結果のレポートを保存"""
    report = {
        "処理日時": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "処理件数": len(results["processed"]),
        "変換件数": len(results["modified"]),
        "エラー件数": len(results["errors"]),
        "変換されたファイル": results["modified"],
        "エラー詳細": results["errors"]
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 処理結果レポートを保存しました: {output_file}")
        return True
    except Exception as e:
        print(f"レポートの保存に失敗しました: {e}")
        return False

def show_summary(path_list):
    """パス一覧の概要を表示"""
    print(f"\n📋 読み込んだパス数: {len(path_list)}")
    
    if len(path_list) > 0:
        print("\n最初の5件のパス:")
        for i, path in enumerate(path_list[:5], 1):
            print(f"  {i}. {path}")
        
        if len(path_list) > 5:
            print(f"  ... 他 {len(path_list) - 5}件")

def main():
    """メイン処理"""
    print("=" * 60)
    print("JSONファイル一括変換ツール")
    print("=" * 60)
    print("条件: 入手方法の「ガイド:」を「イベント:」に変換")
    print("      （Eventが含まれる場合のみ）\n")
    
    # パス一覧のJSONファイルを選択
    print("🔍 パス一覧のJSONファイルを選択してください...")
    json_list_file = select_json_file()
    
    if not json_list_file:
        print("\n❌ ファイルが選択されませんでした。")
        return
    
    print(f"\n📂 選択されたファイル: {json_list_file}")
    
    # JSONファイルを読み込み
    path_list = load_json_file(json_list_file)
    if path_list is None:
        return
    
    if not isinstance(path_list, list):
        print("❌ JSONファイルはパスのリストである必要があります")
        return
    
    # 概要表示
    show_summary(path_list)
    
    # 自動的に処理開始（確認なし）
    print("\n⏳ 処理を自動的に開始します...")
    
    # ベースディレクトリの設定（パスが相対パスの場合）
    base_dir = os.path.dirname(json_list_file)
    print(f"\n📁 ベースディレクトリ: {base_dir}")
    
    # 処理実行
    print("\n" + "=" * 60)
    print("処理開始")
    print("=" * 60)
    
    results = process_card_files(path_list, base_dir)
    
    # 結果表示
    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"✅ 処理件数: {len(results['processed'])}")
    print(f"🔄 変換件数: {len(results['modified'])}")
    print(f"❌ エラー件数: {len(results['errors'])}")
    
    if results["modified"]:
        print("\n--- 変換されたファイル ---")
        for path in results["modified"]:
            print(f"  • {path}")
    
    if results["errors"]:
        print("\n--- エラー詳細 ---")
        for error in results["errors"]:
            print(f"  • {error['path']}: {error['error']}")
    
    # レポート保存
    report_file = os.path.join(os.path.dirname(json_list_file), "変換結果.json")
    save_report(results, report_file)

# テスト用の関数
def test_conversion():
    """変換機能のテスト"""
    test_data = {
        "名前": "テストカード",
        "入手方法": [
            "ガイド: Venusaur Drop Event",
            "パック: 最強の遺伝子",
            "ガイド: 通常のガイド",
            "イベント: その他のイベント"
        ]
    }
    
    print("変換前:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    modified_data, was_modified = convert_guide_to_event(test_data)
    
    print("\n変換後:")
    print(json.dumps(modified_data, ensure_ascii=False, indent=2))
    print(f"\n変換された: {was_modified}")

if __name__ == "__main__":
    try:
        main()
        print("\n" + "=" * 60)
        print("プログラムを終了します")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # テスト実行（必要な場合はコメントを外す）
    # print("\n--- 変換機能のテスト ---")
    # test_conversion()