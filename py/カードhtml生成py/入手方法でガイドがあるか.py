import os
import json
import tkinter as tk
from tkinter import filedialog
import re

def select_folder():
    """フォルダ選択ダイアログを表示し、選択されたフォルダのパスを返す"""
    try:
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを非表示
        root.attributes('-topmost', True)  # ダイアログを最前面に表示
        
        folder_path = filedialog.askdirectory(title="検索を開始するフォルダを選択してください")
        root.destroy()
        
        return folder_path
    except Exception as e:
        print(f"フォルダ選択ダイアログでエラーが発生しました: {e}")
        return None

def natural_sort_key(path):
    """
    パスから数値部分を抽出して自然順ソートのキーを生成
    例: "promo-a/11" → ["promo-a", 11]
    """
    # 正規表現で数値部分とそれ以外を分割
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    
    # "promo-a/19/Greninja.json" のようなパスから数値部分を抽出しやすいように
    # パスを分割して各パーツに対して自然順ソート用のキーを生成
    path_parts = path.split(os.sep)
    
    # ソート用のキーを生成（各パーツを数値と文字列に分割）
    sort_key = []
    for part in path_parts:
        # 英数字を分割して数値はintに変換
        for chunk in re.split('([0-9]+)', part):
            if chunk:
                if chunk.isdigit():
                    sort_key.append(int(chunk))
                else:
                    sort_key.append(chunk.lower())
    
    return sort_key

def search_json_files(folder_path):
    """フォルダ内の全JSONファイルを再帰的に検索し、条件に合うファイルのパスを収集"""
    matched_paths = []
    json_count = 0
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.json'):
                json_count += 1
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # "入手方法"キーが存在し、その値がリストかチェック
                    if "入手方法" in data and isinstance(data["入手方法"], list):
                        # リスト内の各要素をチェック
                        for item in data["入手方法"]:
                            if isinstance(item, str) and "ガイド:" in item:
                                matched_paths.append(file_path)  # パスのみ追加
                                print(f"  ✓ 発見: {os.path.basename(file_path)}")
                                break  # 1つ見つかれば十分
                except (json.JSONDecodeError, UnicodeDecodeError, Exception):
                    # エラーは無視して次へ
                    pass
    
    print(f"\n検索したJSONファイル数: {json_count}")
    
    # 自然順ソートを実行
    if matched_paths:
        print("\n🔄 パスを自然順ソート中...")
        matched_paths.sort(key=natural_sort_key)
    
    return matched_paths

def save_results(matched_paths):
    """結果（パスのみ）を指定されたパスにJSONファイルとして保存"""
    # 指定された保存先
    output_file = "/storage/emulated/0/html/pkpk/ガイド.json"
    
    try:
        # 保存先のディレクトリが存在するか確認
        save_dir = os.path.dirname(output_file)
        if not os.path.exists(save_dir):
            print(f"📁 ディレクトリを作成します: {save_dir}")
            os.makedirs(save_dir, exist_ok=True)
        
        # パスのみのリストをJSONとして保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(matched_paths, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ファイルを保存しました: {output_file}")
        
        # ファイルサイズを表示
        file_size = os.path.getsize(output_file)
        print(f"📄 ファイルサイズ: {file_size} バイト")
        
        return True
    except PermissionError:
        print(f"\n❌ 権限エラー: 保存先に書き込み権限がありません")
        print(f"   保存先: {output_file}")
        return False
    except Exception as e:
        print(f"\n❌ ファイル保存中にエラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("JSONファイル検索ツール")
    print("=" * 60)
    print("条件: '入手方法' に 'ガイド:' を含むJSONファイルの")
    print("      パスのみを抽出して保存します")
    print("      （promo-a/数値 の部分で自然順ソート）\n")
    
    # 保存先の確認
    save_path = "/storage/emulated/0/html/pkpk/ガイド.json"
    print(f"📁 保存先: {save_path}\n")
    
    # フォルダ選択
    print("🔍 検索するフォルダを選択してください...")
    folder_path = select_folder()
    
    if not folder_path:
        print("\n❌ フォルダが選択されませんでした。")
        return
    
    print(f"\n📂 検索フォルダ: {folder_path}")
    print("⏳ 検索中...\n")
    
    # JSONファイル検索（パスのみ収集）
    matched_paths = search_json_files(folder_path)
    
    if matched_paths:
        print(f"\n✅ {len(matched_paths)}個の条件に合致するJSONファイルが見つかりました")
        
        # 見つかったファイルの一覧を表示（ソート済み）
        print("\n--- 見つかったファイルのパス一覧（ソート済み）---")
        for i, path in enumerate(matched_paths, 1):
            # 表示用にパスをそのまま表示
            print(f"{i:2d}. {path}")
        
        # 結果（パスのみ）を保存
        save_results(matched_paths)
            
    else:
        print("\n⚠️  条件に合致するJSONファイルは見つかりませんでした")
        
        # 空の結果も保存
        if save_results([]):
            print("📄 空の結果を保存しました")

# テスト用の関数（実際の実行には影響しません）
def test_sorting():
    """ソート機能のテスト"""
    test_paths = [
        "/storage/emulated/0/html/pkpk/cards/promo-a/19/Greninja.json",
        "/storage/emulated/0/html/pkpk/cards/promo-a/10/Mewtwo.json",
        "/storage/emulated/0/html/pkpk/cards/promo-a/11/Chansey.json",
        "/storage/emulated/0/html/pkpk/cards/promo-a/2/Pikachu.json",
        "/storage/emulated/0/html/pkpk/cards/promo-a/1/Bulbasaur.json",
    ]
    
    print("ソート前:")
    for path in test_paths:
        print(f"  {path}")
    
    test_paths.sort(key=natural_sort_key)
    
    print("\nソート後（自然順）:")
    for path in test_paths:
        print(f"  {path}")

if __name__ == "__main__":
    try:
        main()
        print("\n" + "=" * 60)
        print("処理が完了しました")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # ソート機能のテストを実行する場合はコメントを外す
    # print("\n--- ソート機能のテスト ---")
    # test_sorting()