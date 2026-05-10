import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import os
import re

# ========== 固定パス設定 ==========
# 直接絶対パスを指定（自動計算しない）
INPUT_FOLDER = Path("/storage/emulated/0/html/pkpk/events/release")
OUTPUT_FOLDER = INPUT_FOLDER

def find_json_files(folder_path):
    folder = Path(folder_path)
    return list(folder.glob("*.json"))

def load_json_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_filename(name, keep_spaces=False):
    """ファイル名用に整形"""
    if keep_spaces:
        name = name.replace('/', '_')
        name = name.replace('?', '')
        name = name.replace('*', '')
        name = name.replace('"', '')
        name = name.replace('<', '')
        name = name.replace('>', '')
        name = name.replace('|', '')
        return name
    else:
        name = name.replace(' ', '_')
        name = name.replace('/', '_')
        name = name.replace('?', '')
        name = name.replace('*', '')
        name = name.replace('"', '')
        name = name.replace('<', '')
        name = name.replace('>', '')
        name = name.replace('|', '')
        name = name.replace(':', '_')
        name = name.replace(',', '_')
        name = name.replace('&', 'and')
        name = re.sub(r'_+', '_', name)
        name = name.rstrip('_')
        return name

def extract_series_name(title):
    """タイトルからシリーズ名を抽出"""
    match = re.match(r'^([^(]+)', title)
    if match:
        return match.group(1).strip()
    return title
    
def is_b3_or_higher(series_name):
    """B3以上かどうかを判定（B3, B4, B5..., C1, D2 etc.）"""
    match = re.match(r'^([A-Za-z]+)(\d+)', series_name)
    if match:
        letter = match.group(1).upper()
        number = int(match.group(2))
        
        if letter == 'B' and number >= 3:
            return True
        elif letter > 'B':  # C, D, E...
            return True
    return False

def has_dex_missions(json_data, series_name, title):
    """Dex Missionsを表示するかどうか（B3以上なら常にFalse）"""
    # タイトルからバージョンを抽出してB3以上か判定
    version_match = re.search(r'\(([^)]+)\)', title)
    if version_match:
        version = version_match.group(1)
        match = re.match(r'^([A-Za-z]+)(\d+)', version)
        if match:
            letter = match.group(1).upper()
            number = int(match.group(2))
            # B3以上またはC, D, E... なら非表示
            if (letter == 'B' and number >= 3) or letter > 'B':
                return False
    
    # B3未満の場合は従来通りmissionsの有無で判定
    return bool(json_data.get('missions', []))

def clean_item_name(item_name, series_name):
    """アイテム名からシリーズ名を除去"""
    if f'{series_name}: ' in item_name:
        return item_name.replace(f'{series_name}: ', '')
    return item_name

def get_cover_image_path(item_name, series_name):
    # clean_item_name() を呼ばずに、直接 item_name から (cover) を除去
    base_name = item_name.replace(' (cover)', '').strip()
    
    # コロン+スペースをアンダースコアに変換
    base_name = base_name.replace(': ', '_')
    
    filename = f"{format_filename(base_name, keep_spaces=False)}_cover.webp"
    return f'/images/accessories/covers/{filename}'

def get_emblem_image_path(item_name, series_name):
    filename = format_filename(item_name, keep_spaces=True) + '.webp'
    return f'/images/emblem/{filename}'

def get_backdrop_image_path(item_name, series_name):
    clean_name = clean_item_name(item_name, series_name)
    base_name = clean_name.replace(' (backdrop)', '').strip()
    filename = f"{format_filename(base_name, keep_spaces=False)}_backdrop.webp"
    return f'/images/accessories/backdrops/{filename}'
    
def get_accessory_image_path(item_name, series_name):
    clean_name = clean_item_name(item_name, series_name)
    
    # アクセサリータイプを判定して適切なパスを返す
    if '(playmat)' in item_name:
        base = clean_name.replace(' (playmat)', '').strip()
        filename = f"{format_filename(base, keep_spaces=False)}_playmat.webp"
        return f'/images/accessories/playmats/{filename}'
    
    elif '(card sleeve)' in item_name:
        base = clean_name.replace(' (card sleeve)', '').strip()
        filename = f"{format_filename(base, keep_spaces=False)}_card_sleeve.webp"
        return f'/images/accessories/card_sleeves/{filename}'
    
    elif '(cover)' in item_name:
        # coverは別関数(get_cover_image_path)で処理されるべき
        base = clean_name.replace(' (cover)', '').strip()
        filename = f"{format_filename(base, keep_spaces=False)}_cover.webp"
        return f'/images/accessories/covers/{filename}'
    
    elif '(backdrop)' in item_name:
        # backdropは別関数(get_backdrop_image_path)で処理されるべき
        base = clean_name.replace(' (backdrop)', '').strip()
        filename = f"{format_filename(base, keep_spaces=False)}_backdrop.webp"
        return f'/images/accessories/backdrops/{filename}'
    
    elif '(Pokémon coin)' in item_name or '(Pokemon coin)' in item_name:
        base = clean_name.replace(' (Pokémon coin)', '').replace(' (Pokemon coin)', '').strip()
        filename = f"{format_filename(base, keep_spaces=False)}_Pokémon_coin.webp"
        return f'/images/accessories/coins/{filename}'
    
    else:
        filename = f"{format_filename(clean_name, keep_spaces=False)}.webp"
        return f'/images/accessories/{filename}'


def safe_filename(text, keep_spaces=True):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, '')
    if not keep_spaces:
        text = text.replace(' ', '_')
    text = text.replace(':', '_')
    return text

def safe_url_path(text):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, '')
    return text

def shorten_title(title):
    match = re.match(r'^(.*?release)\s*[-:]\s*', title, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.match(r'^(.*?release)\s+', title, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.match(r'^(.*?release)', title, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.match(r'^([^:]+)', title)
    if match:
        return match.group(1).strip()
    return title

def remove_version_from_set_name(set_name):
    """セット名から (B2a) のようなバージョン情報を除去"""
    return re.sub(r'\s*\([^)]+\)', '', set_name).strip()

def get_dex_missions_path(json_filepath):
    original_name = Path(json_filepath).stem
    if '_release' in original_name:
        set_name = original_name.split('_release')[0]
    else:
        set_name = original_name
    set_name = set_name.replace('_', ' ')
    set_name = remove_version_from_set_name(set_name)
    dex_filename = f"{set_name} Dex Missions.json"
    return f"/data/dex_missions/{dex_filename}"

def get_themed_collections_path(json_filepath):
    original_name = Path(json_filepath).stem
    if '_release' in original_name:
        set_name = original_name.split('_release')[0]
    else:
        set_name = original_name
    set_name = set_name.replace('_', ' ')
    set_name = remove_version_from_set_name(set_name)
    collections_filename = f"{set_name} Themed Collections.json"
    return f"/data/themed_collections/{collections_filename}"
    
def generate_reward_images_config(json_data, series_name):
    reward_images = {}
    
    # 1. shop_items から収集（既存）
    shop_items = json_data.get('shop_items', [])
    for shop in shop_items:
        if shop.get('items'):
            for item in shop['items']:
                item_name = item.get('name', '')
                if '(emblem)' in item_name:
                    image_path = get_emblem_image_path(item_name, series_name)
                    reward_images[item_name] = image_path
                elif '(cover)' in item_name:
                    image_path = get_cover_image_path(item_name, series_name)
                    reward_images[item_name] = image_path
                elif '(backdrop)' in item_name:
                    image_path = get_backdrop_image_path(item_name, series_name)
                    reward_images[item_name] = image_path
                else:
                    image_path = get_accessory_image_path(item_name, series_name)
                    reward_images[item_name] = image_path
    
    # 2. missions（Dex Missions）から収集
    missions = json_data.get('missions', [])
    for mission in missions:
        reward = mission.get('reward', '')
        if reward and isinstance(reward, str):
            # "アイテム名 ×数字" からアイテム名を抽出
            import re
            match = re.match(r'^(.+?)(?:\s*×\d+)?$', reward)
            if match:
                item_name = match.group(1).strip()
                if item_name not in reward_images:
                    if '(profile icon)' in item_name:
                        reward_images[item_name] = get_profile_icon_path(item_name, series_name)
                    elif '(emblem)' in item_name:
                        reward_images[item_name] = get_emblem_image_path(item_name, series_name)
    
    # 3. collections から収集
    collections = json_data.get('collections', [])
    for collection in collections:
        reward = collection.get('reward', [])
        if isinstance(reward, list):
            for r in reward:
                if isinstance(r, dict):
                    item_name = r.get('item', '')
                    if item_name and item_name not in reward_images:
                        if '(profile icon)' in item_name:
                            reward_images[item_name] = get_profile_icon_path(item_name, series_name)
                        elif '(emblem)' in item_name:
                            reward_images[item_name] = get_emblem_image_path(item_name, series_name)
    
    # 4. secret_missions から収集
    secret_missions = json_data.get('secret_missions', [])
    for mission in secret_missions:
        reward = mission.get('reward', [])
        if isinstance(reward, list):
            for r in reward:
                if isinstance(r, dict):
                    item_name = r.get('item', '')
                    if item_name and item_name not in reward_images:
                        if '(profile icon)' in item_name:
                            reward_images[item_name] = get_profile_icon_path(item_name, series_name)
                        elif '(emblem)' in item_name:
                            reward_images[item_name] = get_emblem_image_path(item_name, series_name)
    
    # 5. 基本報酬（動的 Emblem Ticket パス）
    # series_name をファイル名用に整形（コロン → アンダースコア）
    formatted_series_name = series_name.replace(':', '_')
    emblem_ticket_filename = f"Emblem Ticket ({formatted_series_name}).webp"
    emblem_ticket_path = f"/images/tickets/{emblem_ticket_filename}"
    
    basic_rewards = {
        "Emblem Ticket": emblem_ticket_path,
        "Wonder Hourglass": "/images/items/Wonder Hourglass.webp",
        "Pack Hourglass": "/images/items/Pack Hourglass.webp",
        "Shop Ticket": "/images/tickets/Shop ticket.webp"
    }
    
    for key, value in basic_rewards.items():
        if key not in reward_images:
            reward_images[key] = value
    
    return reward_images

def get_profile_icon_path(item_name, series_name):
    """プロフィールアイコンのパスを生成"""
    clean_name = item_name.replace(' (profile icon)', '').strip()
    if clean_name.startswith(f'{series_name}: '):
        clean_name = clean_name.replace(f'{series_name}: ', '')
    filename = f"{format_filename(clean_name, keep_spaces=False)}_icon.webp"
    return f'/images/accessories/icons/{filename}'

def generate_release_html(json_data, json_filepath, output_folder):
    title = json_data['title']
    title = shorten_title(title)
    series_name = extract_series_name(title)
    
    version_match = re.search(r'\(([^)]+)\)', json_data['title'])
    version_suffix = f" ({version_match.group(1)})" if version_match else ""
    series_name_with_version = series_name + version_suffix
    
    period = json_data['period']
    period_text = period['text']
    start_date = period['start_date']
    year = start_date.split('-')[0]
    
    end_date = period.get('end_date')
    if not end_date or end_date == "3000-12-31":
        main_period_text = f"{period_text}, {year} - Ongoing"
    else:
        main_period_text = f"{period_text}, {year}"
    
    game_updates = json_data.get('game_updates', [])
    shop_items = json_data.get('shop_items', [])
    packs = json_data.get('packs', [])
    
    reward_images = generate_reward_images_config(json_data, series_name)
    # rewardImages ラッパーオブジェクトで出力
    reward_images_wrapper = {"rewardImages": reward_images}
    reward_images_json = json.dumps(reward_images_wrapper, ensure_ascii=False, indent=2)
    
    dex_missions_path = get_dex_missions_path(json_filepath)
    themed_collections_path = get_themed_collections_path(json_filepath)
    
    # Dex Missions セクションの画像パスを生成
    dex_filename = series_name_with_version.replace(':', '')
    dex_image_path = f"/images/missions/dex_missions/{dex_filename}.webp"
    
    # Themed Collections セクションの画像パスを生成（コロンを削除）
    collection_filename = series_name_with_version.replace(':', '')
    collection_image_path = f"/images/missions/themed_collections/{collection_filename}.webp"

    
    updates_html = ""
    if game_updates:
        updates_items = '\n'.join([f'          <li>{item}</li>' for item in game_updates])
        updates_html = f'''
    <!-- Game Updates -->
    <div class="section">
      <div class="content">
        <div class="subheading">
          <h2>Game Updates</h2>
        </div>
        <ul class="update-list">
{updates_items}
        </ul>
      </div>
    </div>'''
    
    shop_html = ""
    if shop_items:
        all_items = []
        for shop in shop_items:
            if shop.get('items'):
                for item in shop['items']:
                    item_name = item.get('name', '')
                    price = item.get('price', '')
                    currency = item.get('currency', '')
                    currency_image = item.get('currency_image', '')
                    if currency == 'SHOPTICKET':
                        currency_img = '/images/tickets/Shop ticket.webp'
                    else:
                        currency_img = f'/images/tickets/{currency_image}'
                    if '(emblem)' in item_name:
                        img_path = get_emblem_image_path(item_name, series_name)
                    elif '(cover)' in item_name:
                        img_path = get_cover_image_path(item_name, series_name)
                    elif '(backdrop)' in item_name:
                        img_path = get_backdrop_image_path(item_name, series_name)
                    else:
                        img_path = get_accessory_image_path(item_name, series_name)
                    all_items.append({
                        'name': item_name,
                        'price': price,
                        'currency_img': currency_img,
                        'img_path': img_path
                    })
        if all_items:
            items_html = []
            for item in all_items:
                items_html.append(f'''
          <div class="item">
            <div class="tooltip">
              <img src="{item['img_path']}" alt="{item['name']}" onerror="this.src='/images/placeholder.webp'">
              <span class="tooltiptext">{item['name']}</span>
            </div>
            <div class="Shop-Ticket">
              <img src="{item['currency_img']}" alt="Ticket">
              <span>{item['price']}</span>
            </div>
          </div>''')
            items_grid = f'''
        <div class="accessory-grid">
{''.join(items_html)}
        </div>'''
            shop_html = f'''
    <!-- New shop items -->
    <div class="section">
      <div class="content">
        <div class="subheading">
          <h2>New shop items</h2>
        </div>
        <div class="event-row">
          <div class="label">Release date</div>
          <div class="date">{main_period_text}</div>
        </div>
        <div class="intro">
          <p>New emblems that can be purchased with Emblem Tickets have been added. Emblem Tickets are obtained as mission rewards.</p>
          <p>Additionally, a cover binder themed after this series has been added to the Shop menu. This binder can be purchased with Shop Tickets.</p>
        </div>
{items_grid}
      </div>
    </div>'''
    
    packs_html = ""
    if packs:
        pack_items = []
        for pack in packs:
            pack_title = pack.get('title', '')
            pack_link = pack.get('link', '')
            pack_image = pack.get('key_visual', '')
            pack_items.append(f'''
      <a href="{pack_link}">
        <img src="{pack_image}" alt="{pack_title}" class="featured-pack">
      </a>''')
        packs_html = f'''
    <!-- 目玉カード -->
    <div class="featured-packs">
{''.join(pack_items)}
    </div>'''
    else:
        packs_html = '''
    <!-- 目玉カード -->
    <div class="featured-packs">
      <a href="/sets/a4b/Deluxe Pack ex pack.html">
        <img src="/images/packs/Deluxe Pack ex pack.webp" alt="Deluxe Pack ex pack" class="featured-pack">
      </a>
    </div>'''
    
    set_name = title.split(' release')[0]
    intro_text = f"""<p><strong>{title}</strong> is now available! This expansion introduces new ex cards and exclusive rewards.</p>
<p>New cards from this set can be obtained by opening {set_name} booster packs. Complete missions to earn Emblem Tickets and special items!</p>"""
    
    output_filename = safe_filename(f"{title}.html", keep_spaces=True)
    output_filepath = Path(output_folder) / output_filename
    image_filename = safe_url_path(f"{title}.webp")
    
    # Dex Missionsを表示するか判定
    show_dex_missions = has_dex_missions(json_data, series_name, title)
    
    # Dex Missionsセクション（条件付き）
    dex_missions_html = ""
    if show_dex_missions:
        dex_missions_html = f'''
    <!-- Dex Missions (動的読み込み) -->
    <div class="section">
      <div class="content">
        <div class="subheading">
          <h2>Dex Missions</h2>
        </div>
        
        <!-- キービジュアル -->
        <img src="{dex_image_path}" alt="{series_name} Dex mission" class="hero_image" onerror="this.style.display='none'">
        
        <div class="event-row">
          <div class="label">Release date</div>
          <div class="date">{main_period_text}</div>
        </div>
        <div class="intro">
          <p>Clear these missions to earn Emblem Tickets and exclusive Emblem!</p>
        </div>
        <div id="mission-container" 
             class="mission-group" 
             data-dex-path="{dex_missions_path}">
          <div class="loading">Loading missions...</div>
        </div>
      </div>
    </div>'''
    
    # Themed Collectionsセクション
    themed_collections_html = f'''
    <!-- Themed Collections (動的読み込み) -->
    <div class="section">
      <div class="content">
        <div class="subheading">
          <h2>Themed Collections</h2>
        </div>
        
        <!-- キービジュアル -->
        <img src="{collection_image_path}" alt="{series_name} Themed Collection" class="hero_image" onerror="this.style.display='none'">
        
        <div class="event-row">
          <div class="label">Release date</div>
          <div class="date">{main_period_text}</div>
        </div>
        <div class="intro">
          <p>Complete these missions to earn Emblem Tickets, Wonder Hourglasses, and exclusive Emblem!</p>
        </div>
        <div id="themed-collections-container" 
             class="mission-group" 
             data-collections-path="{themed_collections_path}">
          <div class="loading">Loading themed collections...</div>
        </div>
      </div>
    </div>'''
    
    html_template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/base.css">
  <link rel="stylesheet" href="/styles/tooltip.css">
  <link rel="stylesheet" href="/styles/release.css">
</head>
<body class="page-body">
  <div id="header"></div>
  <nav class="breadcrumbs">
    <a href="/">Top</a>
    <a href="/Events.html">Events</a>
    <a href="/events/release/{output_filename}">{title}</a>
  </nav>
  <main class="page-main">
    <div class="section">
      <h1 class="main-title">{title}</h1>
    </div>
    <img src="/images/events/release/{image_filename}" alt="{title}" class="hero_image">
    <div class="event-row">
      <div class="label">Release date</div>
      <div class="date">{main_period_text}</div>
    </div>
    <div class="intro">
      {intro_text}
    </div>
    {packs_html}
{updates_html}
{shop_html}
{dex_missions_html}
{themed_collections_html}
  </main>
  <div id="footer"></div>
  <script id="missions-config" type="application/json">
{reward_images_json}
  </script>
  <script src="/js/header-footer-load.js"></script>
  <script src="/js/tooltip.js"></script>
  <script src="/js/release-missions.js"></script>
</body>
</html>'''
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"  ✅ 生成完了: {output_filename}")
    return output_filepath

def main():
    # パス確認をメッセージボックスで表示
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    working_folder = INPUT_FOLDER  # 別の変数にコピー
    
    if not working_folder.exists():
        messagebox.showerror("エラー", f"フォルダが見つかりません:\n{working_folder}\n\n手動で選択します")
        # 手動選択にフォールバック
        working_folder = Path(filedialog.askdirectory(title="JSONファイルのあるフォルダを選択"))
        if not working_folder:
            return
    
    json_files = find_json_files(working_folder)
    if not json_files:
        messagebox.showwarning("警告", "JSONファイルが見つかりませんでした。")
        return
    
    successful, failed = [], []
    
    for i, json_file in enumerate(json_files, 1):
        try:
            json_data = load_json_data(json_file)
            output_filepath = generate_release_html(json_data, json_file, working_folder)
            successful.append(str(output_filepath))
        except Exception as e:
            failed.append(json_file.name)
    
    if failed:
        messagebox.showwarning(
            "処理完了（一部エラー）", 
            f"✅ 成功: {len(successful)} 個\n❌ 失敗: {len(failed)} 個\n\n"
            f"失敗したファイル:\n{chr(10).join(failed)}"
        )
    else:
        messagebox.showinfo(
            "完了", 
            f"✅ すべて成功！\n\n{len(successful)} 個のHTMLを生成しました！"
        )
    root.destroy()
    
if __name__ == "__main__":
    main()