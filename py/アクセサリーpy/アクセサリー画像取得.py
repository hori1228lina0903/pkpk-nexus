import os
import re
import urllib.request
from pathlib import Path
import time
import random
from io import BytesIO
from PIL import Image, ImageOps
import numpy as np
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import cloudscraper
import requests

# アクセサリータイプとフォルダ名、サフィックスのマッピング
ACCESSORY_CONFIG = {
    'icon': {
        'folder': 'icons',
        'suffix': 'icon',
        'name_pattern': r'(.+?)\s*\(icon\)'
    },
    'card_sleeves': {
        'folder': 'card_sleeves',
        'suffix': 'card_sleeve',
        'name_pattern': r'(.+?)\s*\(card sleeve\)'
    },
    'covers': {
        'folder': 'covers',
        'suffix': 'cover',
        'name_pattern': r'(.+?)\s*\(cover\)'
    },
    'coins': {
        'folder': 'coins',
        'suffix': 'Pokémon_coin',
        'name_pattern': r'(.+?)\s*\(Pokémon coin\)'
    },
    'backdrops': {
        'folder': 'backdrops',
        'suffix': 'backdrop',
        'name_pattern': r'(.+?)\s*\(backdrop\)'
    },
    'playmats': {
        'folder': 'playmats',
        'suffix': 'playmat',
        'name_pattern': r'(.+?)\s*\(playmat\)'
    }
}

# HTMLファイルのパス
HTML_FILES = {
    'icon': '/storage/emulated/0/html/pkpk/ソースhtml/アイコン.html',
    'coins': '/storage/emulated/0/html/pkpk/ソースhtml/コイン.html',
    'covers': '/storage/emulated/0/html/pkpk/ソースhtml/カバー.html',
    'backdrops': '/storage/emulated/0/html/pkpk/ソースhtml/バックドロップ.html',
    'playmats': '/storage/emulated/0/html/pkpk/ソースhtml/プレイマット.html',
    'card_sleeves': '/storage/emulated/0/html/pkpk/ソースhtml/カードスリーブ.html'
}

# 保存先のベースディレクトリ
BASE_SAVE_DIR = Path('/storage/emulated/0/html/pkpk/images/accessories')

# ランダムUser-Agentの候補リスト
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Cloudscraperの設定
try:
    scraper = cloudscraper.create_scraper(
        delay=5,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
        }
    )
    use_cloudscraper = True
    print("✅ Cloudscraperを使用します")
except Exception as e:
    use_cloudscraper = False
    print(f"⚠️ Cloudscraperが使用できません: {e}")

def fetch_with_retry(url, max_retries=3):
    """リトライ機能付きリクエスト"""
    for attempt in range(max_retries):
        try:
            headers = {
                "User-Agent": random.choice(user_agents),
                "Referer": "https://www.pokemon-zone.com/",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            }
            
            if use_cloudscraper and scraper:
                resp = scraper.get(url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    return resp.content
            else:
                # requestsを使ったフォールバック
                resp = requests.get(url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    return resp.content
            
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"   リトライ {attempt+2}/{max_retries} - {wait_time}秒待機")
                time.sleep(wait_time)
        except Exception as e:
            print(f"   エラー (試行{attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None

def extract_items_from_html(html_content: str, category: str) -> List[Dict[str, str]]:
    """HTMLから商品名と画像URLを抽出する（大きな画像を優先）"""
    items = []
    soup = BeautifulSoup(html_content, 'html.parser')
    config = ACCESSORY_CONFIG[category]
    
    for item_div in soup.find_all('div', class_=re.compile(r'pz-paper')):
        # 商品名を取得
        name_div = item_div.find('div', class_='font-bold')
        if not name_div:
            continue
        
        full_name = name_div.get_text().strip()
        
        # パターンからベース名を抽出
        match = re.search(config['name_pattern'], full_name)
        if match:
            base_name = match.group(1).strip()
        else:
            base_name = re.sub(r'\s*\([^)]+\)', '', full_name).strip()
        
        # すべてのimgタグを取得
        img_tags = item_div.find_all('img')
        if not img_tags:
            continue
        
        # 大きな画像を探す（2番目のimgタグが大きな画像）
        # カードスリーブ: 2番目のimg、プレイマット: 2番目のimg
        main_img = None
        
        if len(img_tags) >= 2:
            # 2番目の画像が大きな画像
            main_img = img_tags[1]
        else:
            # フォールバック: 最初の画像
            main_img = img_tags[0]
        
        img_url = main_img.get('src', '')
        if not img_url:
            continue
        
        # URLを完全な形に整形（?width=400などのパラメータはそのまま維持）
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = 'https://www.pokemon-zone.com' + img_url
        
        # 大きな画像を得るために、widthパラメータを大きくするか削除
        # 元の大きな画像を取得するため、パラメータを調整
        if '?width=100' in img_url:
            # サムネイルURLの場合、より大きなサイズに変更
            img_url = img_url.replace('?width=100', '?width=800')
        elif 'width=400' in img_url:
            # すでに大きな画像ならそのまま、またはさらに大きく
            img_url = img_url.replace('width=400', 'width=800')
        
        # カードスリーブとプレイマットは特別処理
        # Texturesディレクトリの画像を優先（プレイマット用）
        if category == 'playmats' and '/Textures/' not in img_url:
            # Texturesパスを試す
            alt_url = img_url.replace('/L/Materials/', '/Textures/')
            alt_url = alt_url.replace('_DeckShield_PAR1', '_PlayMat_T')
            # 元のURLも保持するが、Texturesの方が良い場合がある
            # ここでは両方試せるように元のURLを使う
        
        items.append({
            'base_name': base_name,
            'full_name': full_name,
            'url': img_url,
            'suffix': config['suffix'],
            'extension': '.webp',
        })
    
    return items

def sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を除去する"""
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = name.replace(' ', '_')
    name = name.replace('&', 'and')
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    # 長すぎる名前を短縮
    if len(name) > 100:
        name = name[:100]
    return name

def add_noise_to_rgb_only(img, noise_strength=5):
    """画像のRGB部分にのみノイズを追加"""
    if img.mode == 'RGBA':
        rgb = img.convert('RGB')
        alpha = img.split()[-1]
        
        np_rgb = np.array(rgb).astype(np.int16)
        noise = np.random.normal(0, noise_strength, np_rgb.shape)
        noisy_rgb = np.clip(np_rgb + noise, 0, 255).astype(np.uint8)
        
        noisy_img = Image.fromarray(noisy_rgb)
        noisy_img.putalpha(alpha)
        return noisy_img
    else:
        np_img = np.array(img).astype(np.int16)
        noise = np.random.normal(0, noise_strength, np_img.shape)
        noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_img)

def crop_one_pixel(img):
    """上下左右1pxずつカット"""
    width, height = img.size
    if width > 2 and height > 2:
        return img.crop((1, 1, width - 1, height - 1))
    return img

def download_and_process_image(item: Dict[str, str], save_dir: Path):
    """画像をダウンロードして加工"""
    url = item['url']
    base_name = item['base_name']
    suffix = item['suffix']
    
    print(f"   Downloading: {base_name}")
    print(f"   URL: {url}")
    
    # ランダム待機（過剰アクセス防止）
    time.sleep(random.uniform(2, 5))
    
    image_data = fetch_with_retry(url)
    
    if image_data is None:
        print(f"    ❌ ダウンロード失敗")
        return False
    
    if len(image_data) == 0:
        print(f"    ❌ 空のデータ")
        return False
    
    try:
        # PILで画像を開く
        img = Image.open(BytesIO(image_data))
        original_size = img.size
        print(f"    画像サイズ: {original_size[0]}x{original_size[1]}")
        
        # 加工
        img = add_noise_to_rgb_only(img, noise_strength=5)
        img = crop_one_pixel(img)
        
        # 保存
        clean_name = sanitize_filename(base_name)
        filename = f"{clean_name}_{suffix}.webp"
        save_path = save_dir / filename
        
        save_dir.mkdir(parents=True, exist_ok=True)
        img.save(save_path, format="WEBP", quality=80)
        
        saved_size = save_path.stat().st_size
        print(f"    ✅ 保存: {filename} ({saved_size} bytes)")
        return True
        
    except Exception as e:
        print(f"    ❌ 処理エラー: {e}")
        return False

def process_category(category: str):
    """指定カテゴリの画像をダウンロード"""
    html_path = HTML_FILES.get(category)
    if not html_path:
        print(f"エラー: カテゴリ '{category}' に対応するHTMLがありません")
        return
    
    config = ACCESSORY_CONFIG[category]
    folder_name = config['folder']
    save_dir = BASE_SAVE_DIR / folder_name
    
    print(f"\n{'='*50}")
    print(f"カテゴリ: {category}")
    print(f"HTML: {html_path}")
    print(f"保存先: {save_dir}")
    print('-' * 50)
    
    if not Path(html_path).exists():
        print(f"エラー: HTMLファイルが見つかりません - {html_path}")
        return
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        items = extract_items_from_html(html_content, category)
        print(f"商品数: {len(items)} 件")
        
        if not items:
            print("商品が見つかりませんでした")
            return
        
        items.sort(key=lambda x: x['base_name'])
        
        success_count = 0
        
        for i, item in enumerate(items, 1):
            print(f"\n  [{i}/{len(items)}] {item['base_name']}")
            
            # 既存ファイルチェック
            clean_name = sanitize_filename(item['base_name'])
            save_path = save_dir / f"{clean_name}_{item['suffix']}.webp"
            
            if save_path.exists():
                print(f"    スキップ (既存): {save_path.name}")
                continue
            
            if download_and_process_image(item, save_dir):
                success_count += 1
            
            # リクエスト間隔を空ける
            time.sleep(random.uniform(1, 3))
        
        print(f"\n完了: {success_count} 件の新しい画像をダウンロード")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def show_menu() -> Optional[List[str]]:
    """カテゴリ選択メニュー"""
    print("\n" + "=" * 60)
    print("ポケモンTCGポケット アクセサリー画像ダウンローダー")
    print("=" * 60)
    print("\nダウンロードするカテゴリを選択してください：")
    print("1) アイコン")
    print("2) カードスリーブ")
    print("3) カバー")
    print("4) コイン")
    print("5) バックドロップ")
    print("6) プレイマット")
    print("7) すべてダウンロード")
    print("0) 終了")
    
    category_map = {
        '1': ['icon'],
        '2': ['card_sleeves'],
        '3': ['covers'],
        '4': ['coins'],
        '5': ['backdrops'],
        '6': ['playmats'],
        '7': list(HTML_FILES.keys())
    }
    
    while True:
        choice = input("\n選択 (0-7): ").strip()
        if choice == '0':
            return None
        elif choice in category_map:
            return category_map[choice]
        else:
            print("無効な選択です。0-7の数字を入力してください。")

def main():
    print("=" * 60)
    print("ポケモンTCGポケット アクセサリー画像ダウンローダー")
    print("=" * 60)
    print(f"保存先: {BASE_SAVE_DIR}")
    
    categories = show_menu()
    
    if categories is None:
        print("\n終了します。")
        return
    
    for category in categories:
        process_category(category)
    
    print("\n" + "=" * 60)
    print("すべての処理が完了しました！")

if __name__ == "__main__":
    main()