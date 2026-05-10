import json
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from pathlib import Path
import os
import re
from urllib.parse import urlparse

def select_folder():
    """フォルダ選択ダイアログを表示してフォルダを選択"""
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない
    root.attributes('-topmost', True)  # ダイアログを最前面に
    
    folder_path = filedialog.askdirectory(
        title="JSONファイルが格納されているフォルダを選択してください"
    )
    
    root.destroy()
    return folder_path

def find_json_files(folder_path):
    """フォルダ内のすべてのJSONファイルを再帰的に検索"""
    folder = Path(folder_path)
    json_files = list(folder.rglob("*.json"))  # サブフォルダも含むすべてのJSONファイル
    return json_files

def load_json_data(filepath):
    """JSONファイルを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_premium_pass_html(json_data, json_filepath):
    """JSONデータからプレミアムパスHTMLを生成"""
    # デバッグ用：実際の値を確認
    print(f"処理中: {Path(json_filepath).name}")
    print("  period:", json_data['period'])
    print("  start_date:", json_data['period']['start_date'])
    
    # start_dateから年を取得（例： "2025-04-01" → "2025"）
    start_date = json_data['period']['start_date']
    year = start_date.split('-')[0]  # "2025"を取得
    print("  year:", year)
    
    # 期間テキスト（表示用）
    period_text = json_data['period']['text']
    print("  period_text:", period_text)
    
    # 開始月を抽出（例： "Apr 1 - Jun 1" → "Apr"）
    month_map = {
        'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
        'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
        'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
    }
    
    start_month_abbr = period_text.split()[0]
    start_month_full = month_map.get(start_month_abbr, start_month_abbr)
    print("  start_month_full:", start_month_full)
    
    # 出力ファイル名
    output_filename = f"Premium Pass ({start_month_full} {year}).html"
    print("  output_filename:", output_filename)
    
    # 出力ファイルパス（元のJSONと同じフォルダに出力）
    json_path = Path(json_filepath)
    output_filepath = json_path.parent / output_filename
    
    # ページタイトル
    page_title = f"Premium Pass ({start_month_full} {year})"
    
    # === カード情報をURLから抽出 ===
    card_url = json_data['premium_card']['url']
    
    # URLからパス部分を抽出 (例: /cards/promo-a/93/cleffa/)
    parsed_url = urlparse(card_url)
    card_path = parsed_url.path.rstrip('/')  # 最後の/を除去
    
    # パスを分割 (例: ['', 'cards', 'promo-a', '93', 'cleffa'])
    path_parts = card_path.split('/')
    
    # cards/以降の部分を取得
    if 'cards' in path_parts:
        cards_index = path_parts.index('cards')
        # セット名と番号を取得 (promo-a/93)
        if len(path_parts) > cards_index + 2:
            card_set = path_parts[cards_index + 1]  # promo-a
            card_number = path_parts[cards_index + 2]  # 93
            card_id = f"{card_set}/{card_number}"  # promo-a/93
        else:
            card_id = ""
        
        # カード名を取得 (ex. "cleffa", "mewtwo-ex", "zapdos-ex")
        if len(path_parts) > cards_index + 3:
            card_name_raw = path_parts[cards_index + 3]  # "mega-absol-ex"
            
            if card_name_raw:
                # ファイル名用：ハイフンをアンダースコアに変換して最初を大文字
                card_name = card_name_raw.replace('-', '_').replace('@', '-')
                card_name = card_name[0].upper() + card_name[1:]  # "Mega_absol_ex"
                
                # 表示用（alt属性）：@を-に変換して、-を_に変換
                card_name_display = card_name_raw.replace('-', '_').replace('@', '-')  # "chien_pao_ex"
                
                # 報酬名マッチング用：ハイフンをスペースに変換
                card_name_for_matching = card_name_raw.replace('@', '-').replace('-', ' ')  # "chien pao ex"
            else:
                card_name = ""
                card_name_display = ""
                card_name_for_matching = ""
        else:
            card_name = ""
            card_name_display = ""
            card_name_for_matching = ""
    else:
        card_id = ""
        card_name = ""
        card_name_display = ""
        card_name_for_matching = ""
    
    print(f"  カードID: {card_id}")
    print(f"  カード名（ファイル用）: {card_name}")
    print(f"  カード名（表示用）: {card_name_display}")
    print(f"  カード名（マッチング用）: {card_name_for_matching}")
    
    # ミッションデータ
    missions_data = json_data['missions'][0]['missions']
    
    # アクセサリーアイテムのHTML生成
    accessory_html = generate_accessory_items(json_data['premium_items'][0]['items'])
    
    # ミッションカードのHTML生成（マッチング用のカード名とカード情報を渡す）
    mission_html = generate_mission_cards(missions_data, card_name_for_matching, card_id, card_name, card_name_display)
    
    # メイン期間に年を追加（JSONに年がない場合）
    main_period_text = json_data['period']['text']
    if ',' not in main_period_text:
        # カンマがない場合は年を追加
        main_period_text = f"{main_period_text}, {year}"
    
    # キービジュアル画像のファイル名を生成
    hero_image_name = f"premium_pass_hero_image_{start_month_full.lower()}_{year}.webp"
    
    # HTMLテンプレート - URLから抽出した値を使用
    html_template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>{page_title}</title>

  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/base.css">
  <link rel="stylesheet" href="/styles/tooltip.css">
   <link rel="stylesheet" href="/styles/premium_pass.css">
</head>

<body class="page-body">

  <div id="header"></div>

  <nav class="breadcrumbs">
    <a href="/">Home</a>
    <a href="/Events.html">Events</a>
    <a href="/Events/{output_filename}">{page_title}</a>
  </nav>

  <main class="page-main">

    <div class="section">
      <h1 class="main-title">
        Premium Pass Update
        <span class="sub-title">({start_month_full} {year})</span>
      </h1>
    </div>
    
    <!-- キービジュアル -->
    <img src="/images/events/premium_pass/{hero_image_name}" alt="{card_name_display}" class="hero_image">
    
    <!-- 開催期間 -->
    <div class="event-row">
      <div class="label">
        Event period
      </div>
      <div class="date">
        {main_period_text}
      </div>
    </div>

    <!-- 見出し文章 -->
    <div class="intro">
      <p>
        The {start_month_full} {year} Premium Pass in Pokémon TCG Pocket introduces a new selection of exclusive rewards available in the Premium Shop. These items are only available for a limited time and can be obtained exclusively by players with an active Premium Pass subscription.
      </p>

      <p>
        One of the highlights of the {start_month_full} {year} Premium Pass rewards is the Art Rare promo card, which is available as this month’s login reward. Players who log in to Pokémon TCG Pocket while their Premium Pass is active will automatically complete the mission and can claim the promo card as a reward.
      </p>
    </div>

    <!-- 目玉カード -->
    <div class="featured-item">
      <a href="/cards/{card_id}/{card_name}.html">
        <img src="/images/cards/{card_id}.webp" alt="{card_name_display}" class="featured-card">
      </a>
    </div>

    <!-- プレミアムショップ -->
    <div class="section">
      <div class="content">

        <div class="subheading">
          <h2>Premium Shop Accessories
            <br>({start_month_full} {year})
          </h2>
        </div>

        <!-- 開催期間 -->
        <div class="event-row">
          <div class="label">
            Event period
          </div>
          <div class="date">
            {json_data['premium_items'][0]['period']}
          </div>
        </div>
        
        <!-- 交換アクセサリー -->
        <div class="accessory-grid">
{accessory_html}
        </div>
          
          <div class="intro">
            <p>Available only to players with the Premium Pass.</p>
          </div>
      </div>
    </div>

    <!-- プレミアムミッション -->
    <div class="section">
      <div class="content">
    
        <div class="subheading">
          <h2>Premium Missions
            <br>({start_month_full} {year})
          </h2>
        </div>
        
        <!-- 開催期間 -->
        <div class="event-row">
          <div class="label">Event period</div>
          <div class="date">{json_data['missions'][0]['period']}</div>
        </div>
        
        <!-- 説明文 -->
        <div class="intro">
          <p>
            Premium Missions are special missions available to Premium Pass subscribers in Pokémon TCG Pocket. Completing these missions rewards Premium Tickets that can be used to purchase accessories in the Premium Shop. Premium Missions are refreshed monthly.
          </p>
        </div>
    
        <!-- ミッション一覧 -->
        <div class="mission-group">
          <div class="mission-list">
{mission_html}
          </div>
        </div>

      </div>
    </div>
    
  </main>

  <div id="footer"></div>

  <script src="/js/header-footer-load.js"></script>
  <script src="/js/tooltip.js"></script>

</body>
</html>'''
    
    # HTMLをファイルに書き込み
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"  ✅ 生成完了: {output_filename}")
    return output_filepath

def get_card_image_path(card_data):
    """カードの画像パスを取得"""
    # カード名やIDから画像パスを生成
    if 'id' in card_data and card_data['id']:
        # 例: /images/cards/a2b/5.webp
        return f"/images/cards/{card_data['id']}.webp"
    elif 'url' in card_data and card_data['url']:
        # URLからIDを抽出する処理など
        return "/images/placeholder.webp"
    else:
        return "/images/placeholder.webp"

def generate_accessory_items(items):
    """アクセサリーアイテムのHTMLを生成（ツールチップ付き）"""
    
    # 表示順序を定義する関数
    def get_order(item_name):
        name_lower = item_name.lower()
        if 'coin' in name_lower:
            return 1
        elif 'playmat' in name_lower:
            return 2
        elif 'card sleeve' in name_lower:
            return 3
        elif 'backdrop' in name_lower:
            return 4
        elif 'cover' in name_lower:
            return 5
        else:
            return 999
    
    # 順序でソート
    sorted_items = sorted(items, key=lambda x: get_order(x['name']))
    
    # HTML生成
    html_lines = []
    for item in sorted_items:
        img_path = generate_accessory_filename(item['name'])
        
        # 説明文を取得（descriptionフィールドがあれば使用、なければ名前を使用）
        description = item.get('description', item['name'])
        
        html_lines.append(f'''          <div class="item tooltip">
            <img src="/images/accessories/{img_path}" alt="{item['name']}">
            <span class="tooltiptext">{description}</span>
            <div class="Premium-Ticket">
              <img src="/images/items/Premium Ticket.webp" alt="Premium Ticket">
              <span>{item['price']}</span>
            </div>
          </div>''')
    
    return '\n'.join(html_lines)

def generate_accessory_filename(item_name):
    """アイテム名からアクセサリー画像のファイル名を生成（サブフォルダ込み）"""
    
    # 種類を特定するための小文字版（判定用）
    name_lower = item_name.lower()
    
    # 括弧の前の部分をテーマ名として抽出（元のケースを保持）
    if '(' in item_name:
        theme = item_name.split('(')[0].strip()
    else:
        theme = item_name.strip()
    
    # & を and に変換してから、スペースをアンダースコアに変換
    theme = theme.replace('&', 'and').replace(' ', '_')
    
    # 種類を判別してファイル名を生成
    if 'pokémon coin' in name_lower or 'coin' in name_lower:
        return f"coins/{theme}_Pokémon_coin.webp"
    elif 'card sleeve' in name_lower:
        return f"card_sleeves/{theme}_card_sleeve.webp"
    elif 'playmat' in name_lower:
        return f"playmats/{theme}_playmat.webp"
    elif 'backdrop' in name_lower:
        return f"backdrops/{theme}_backdrop.webp"
    elif 'cover' in name_lower:
        return f"covers/{theme}_cover.webp"
    else:
        return f"other/{theme}.webp"

def generate_mission_cards(missions, premium_card_name, premium_card_id, card_name, card_name_display):
    """ミッションカードのHTMLを生成（1日目のプロモカードにリンクを追加）"""
    html_lines = []
    
    for i, mission in enumerate(missions, 1):
        description = mission['description']
        rewards = mission['rewards']
        
        # プレビューアイテムの生成
        preview_items = []
        for reward in rewards:
            img_path, alt, amount, is_promo_card = get_reward_image_info(reward, premium_card_name, premium_card_id)
            
            # プロモカード（1日目の報酬）の場合はリンクを追加
            if is_promo_card:
                preview_items.append(f'''                  <div class="mission-card__preview-item">
                    <a href="/cards/{premium_card_id}/{card_name}.html">
                      <img src="{img_path}" alt="{alt}">
                    </a>
                    <span>×{amount}</span>
                  </div>''')
            else:
                preview_items.append(f'''                  <div class="mission-card__preview-item">
                    <img src="{img_path}" alt="{alt}">
                    <span>×{amount}</span>
                  </div>''')
        
        # 説明文にレアリティ記号がある場合の処理
        description = process_description(description)
        
        html_lines.append(f'''            <!-- {i}. {strip_html(description)} -->
            <div class="mission-card">
              <div class="mission-card__inner">
                <div class="mission-card__preview">
{chr(10).join(preview_items)}
                </div>
                <div class="mission-card__content">
                  <div class="mission-card__text">{description}</div>
                </div>
              </div>
            </div>''')
    
    return '\n'.join(html_lines)

def get_reward_image_info(reward, premium_card_name, premium_card_id):
    reward_name = reward['name'].lower()
    amount = reward.get('amount', '1')
    is_promo_card = False
    
    # デバッグ出力（スクリプトのあるフォルダにdebug_match.txtを作成）
    import os
    debug_file = os.path.join(os.path.dirname(__file__), 'debug_match.txt')
    with open(debug_file, 'a', encoding='utf-8') as f:
        f.write(f"reward_name: {reward_name}\n")
        f.write(f"premium_card_name: {premium_card_name}\n")
        f.write(f"premium_card_id: {premium_card_id}\n")
        f.write("---\n")
    
    img_path = '/images/items/Placeholder.webp'
    alt = reward['name']
    
    if 'premium ticket' in reward_name:
        img_path = '/images/items/Premium Ticket.webp'
        alt = 'Premium Ticket'
    elif 'pack hourglass' in reward_name:
        img_path = '/images/items/Pack Hourglass.webp'
        alt = 'Pack Hourglass'
    elif 'wonder hourglass' in reward_name:
        img_path = '/images/items/Wonder Hourglass.webp'
        alt = 'Wonder Hourglass'
    elif 'shinedust' in reward_name:
        img_path = '/images/items/Shinedust.webp'
        alt = 'Shinedust'
    elif 'trade token' in reward_name:
        img_path = '/images/items/Trade Tokens.webp'
        alt = 'Trade Token'
    else:
        if premium_card_name:
            reward_name_clean = reward_name.replace('1x ', '').replace('2x ', '').replace('3x ', '')
            
            card_variants = [
                premium_card_name.lower(),                           # "chien pao ex"
                premium_card_name.lower().replace(' ', '-'),         # "chien-pao-ex"
                premium_card_name.lower().replace(' ', ''),          # "chienpaoex"
                premium_card_name.lower().replace(' ', '-').replace('-ex', ' ex'),  # "chien-pao ex"
                premium_card_name.lower().replace('@', '-'),         # ← 追加: @を-に変換 "chien-pao ex"
            ]
            
            # デバッグ：バリエーションも記録
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"reward_name_clean: {reward_name_clean}\n")
                f.write(f"card_variants: {card_variants}\n")
            
            for variant in card_variants:
                if variant in reward_name_clean:
                    is_promo_card = True
                    with open(debug_file, 'a', encoding='utf-8') as f:
                        f.write(f"MATCH! variant: {variant}\n")
                    break
        
        if is_promo_card:
            img_path = f'/images/cards/{premium_card_id}.webp'
            alt = reward['name'].replace('1x ', '').replace('×', '').strip()
    
    return img_path, alt, amount, is_promo_card

def process_description(description):
    """説明文を処理（レアリティ記号など）"""
    if '     ' in description:  # レアリティ記号が含まれる場合
        if '50' in description:
            return 'Collect 50 <span class="rarity-stars"><img src="/images/rarities/diamond.webp" alt="Diamond"></span> cards'
        elif '20' in description:
            return 'Collect 20 <span class="rarity-stars"><img src="/images/rarities/diamond.webp" alt="Diamond"><img src="/images/rarities/diamond.webp" alt="Diamond"></span> cards'
    return description

def strip_html(text):
    """HTMLタグを除去（コメント用）"""
    import re
    return re.sub('<[^<]+?>', '', text)

def main():
    """メイン処理"""
    print("=== プレミアムパス一括HTML生成ツール ===")
    print("フォルダを選択すると、中のすべてのJSONファイルをHTMLに変換します\n")
    
    # フォルダを選択
    folder_path = select_folder()
    
    if not folder_path:
        print("フォルダが選択されませんでした。")
        return
    
    print(f"選択されたフォルダ: {folder_path}")
    
    # JSONファイルを検索
    json_files = find_json_files(folder_path)
    
    if not json_files:
        print("フォルダ内にJSONファイルが見つかりませんでした。")
        messagebox.showwarning("警告", "選択されたフォルダ内にJSONファイルが見つかりませんでした。")
        return
    
    print(f"\n📁 {len(json_files)}個のJSONファイルが見つかりました。")
    
    # 処理結果を保存
    successful = []
    failed = []
    
    # 各JSONファイルを処理
    for i, json_file in enumerate(json_files, 1):
        print(f"\n--- 処理中 {i}/{len(json_files)} ---")
        try:
            json_data = load_json_data(json_file)
            output_filepath = generate_premium_pass_html(json_data, json_file)
            successful.append(str(output_filepath))
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            failed.append(str(json_file))
    
    # 結果表示
    print("\n" + "="*50)
    print(f"✅ 処理完了: {len(successful)}個成功")
    if failed:
        print(f"❌ 失敗: {len(failed)}個")
        for f in failed:
            print(f"  - {f}")
    
    # 完了ダイアログ
    root = tk.Tk()
    root.withdraw()
    
    if failed:
        messagebox.showwarning(
            "処理完了（一部エラー）", 
            f"HTML生成が完了しました。\n\n"
            f"✅ 成功: {len(successful)}個\n"
            f"❌ 失敗: {len(failed)}個\n\n"
            f"失敗したファイルはコンソールで確認してください。"
        )
    else:
        messagebox.showinfo(
            "完了", 
            f"すべてのJSONファイルのHTML生成が完了しました！\n\n"
            f"✅ 変換したファイル数: {len(successful)}個\n\n"
            f"出力先:\n{Path(folder_path) / 'Premium Pass (*)'}"
        )
    
    root.destroy()

if __name__ == "__main__":
    main()