import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re

def select_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title="JSONファイルが格納されているフォルダを選択してください")
    root.destroy()
    return folder_path

def find_json_files(folder_path):
    folder = Path(folder_path)
    return list(folder.rglob("*.json"))

def load_json_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_promo_card_names(promo_cards):
    if not promo_cards:
        return "promo cards"
    names = [card['name'].replace(' Rare', '') for card in promo_cards]
    if len(names) == 1:
        return names[0]
    return f"{names[0]} and {names[1]}"

def strip_html(text):
    return re.sub('<[^<]+?>', '', text)

def extract_shinedust_amount(item_name):
    match = re.search(r'(\d+)x?\s*Shinedust', item_name, re.IGNORECASE)
    return match.group(1) if match else "50"

def process_mission_description(description):
    return description
    
def generate_pattern_buttons(patterns_count):
    """パターン数に応じてボタンのHTMLを生成"""
    if patterns_count == 0:
        return ''
    buttons = []
    for i in range(1, patterns_count + 1):
        active_class = 'active' if i == 1 else ''
        buttons.append(f'<button data-pattern="{i}" class="{active_class}">pattern {i}</button>')
    return '\n'.join(buttons)

def generate_bonus_patterns(bonus_picks):
    patterns = {}
    for idx, pick in enumerate(bonus_picks, 1):
        items = pick.get('items', [])
        
        if len(items) >= 5:
            top_row = items[:3]
            bottom_row = items[3:5]
        elif len(items) >= 3:
            top_row = items[:3]
            bottom_row = items[3:]
        else:
            top_row = items
            bottom_row = []
        
        rows = []
        
        # 上段のデータ生成
        top_row_data = []
        for item in top_row:
            item_type = item.get('type', 'item')
            if item_type == 'card':
                src = f"/images/cards/{item.get('id', '')}.webp"
                alt = item.get('name', 'Card')
                url = item.get('url', '')
                if url:
                    parts = url.rstrip('/').split('/')
                    filename = parts[-1]
                    words = filename.split('-')
                    filename = '_'.join(word.capitalize() for word in words)
                    url = '/'.join(parts[:-1]) + '/' + filename + '.html'
                else:
                    card_id = item.get('id', '')
                    card_name = item.get('name', '').replace(' ', '_')
                    url = f"/cards/{card_id}/{card_name}.html"
                top_row_data.append({'type': item_type, 'src': src, 'alt': alt, 'url': url})
            else:
                item_name = item.get('name', '')
                if 'event shop ticket' in item_name.lower() or 'shop ticket' in item_name.lower():
                    src = "/images/tickets/Shop ticket.webp"
                elif 'wonder hourglass' in item_name.lower():
                    src = "/images/items/Wonder Hourglass.webp"
                elif 'pack hourglass' in item_name.lower():
                    src = "/images/items/Pack Hourglass.webp"
                else:
                    image_url = item.get('image_url', '')
                    filename = image_url.split('/')[-1] if image_url else ''
                    src = f"/images/items/{filename}"
                top_row_data.append({'type': item_type, 'src': src, 'alt': item_name})
        rows.append(top_row_data)
        
        # 下段のデータ生成（あれば）
        if bottom_row:
            bottom_row_data = []
            for item in bottom_row:
                item_type = item.get('type', 'item')
                if item_type == 'card':
                    src = f"/images/cards/{item.get('id', '')}.webp"
                    alt = item.get('name', 'Card')
                    url = item.get('url', '')
                    if url:
                        parts = url.rstrip('/').split('/')
                        filename = parts[-1]
                        words = filename.split('-')
                        filename = '_'.join(word.capitalize() for word in words)
                        url = '/'.join(parts[:-1]) + '/' + filename + '.html'
                    else:
                        card_id = item.get('id', '')
                        card_name = item.get('name', '').replace(' ', '_')
                        url = f"/cards/{card_id}/{card_name}.html"
                    bottom_row_data.append({'type': item_type, 'src': src, 'alt': alt, 'url': url})
                else:
                    item_name = item.get('name', '')
                    if 'event shop ticket' in item_name.lower() or 'shop ticket' in item_name.lower():
                        src = "/images/tickets/Shop ticket.webp"
                    elif 'wonder hourglass' in item_name.lower():
                        src = "/images/items/Wonder Hourglass.webp"
                    elif 'pack hourglass' in item_name.lower():
                        src = "/images/items/Pack Hourglass.webp"
                    else:
                        image_url = item.get('image_url', '')
                        filename = image_url.split('/')[-1] if image_url else ''
                        src = f"/images/items/{filename}"
                    bottom_row_data.append({'type': item_type, 'src': src, 'alt': item_name})
            rows.append(bottom_row_data)
        
        patterns[str(idx)] = {'rows': rows}
    
    return patterns

def generate_chansey_patterns(rare_picks):
    patterns = {}
    for idx, pick in enumerate(rare_picks, 1):
        items = pick.get('items', [])
        if len(items) >= 5:
            rows = []
            for row_items in [items[:3], items[3:5]]:
                row_data = []
                for item in row_items:
                    item_type = item.get('type', 'card')
                    if item_type == 'card':
                        src = f"/images/cards/{item.get('id', '')}.webp"
                        alt = item.get('name', 'Card')
                        url = item.get('url', '')
                        if url:
                            parts = url.rstrip('/').split('/')
                            filename = parts[-1]
                            words = filename.split('-')
                            filename = '_'.join(word.capitalize() for word in words)
                            url = '/'.join(parts[:-1]) + '/' + filename + '.html'
                        else:
                            card_id = item.get('id', '')
                            card_name = item.get('name', '').replace(' ', '_')
                            url = f"/cards/{card_id}/{card_name}.html"
                        row_data.append({'type': item_type, 'src': src, 'alt': alt, 'url': url})
                    else:
                        item_name = item.get('name', '')
                        if 'event shop ticket' in item_name.lower() or 'shop ticket' in item_name.lower():
                            src = "/images/items/EVENT_SHOPTICKET_02.webp"
                            alt = item_name
                        elif 'wonder hourglass' in item_name.lower():
                            src = "/images/items/Wonder Hourglass.webp"
                            alt = "Wonder Hourglass"
                        elif 'pack hourglass' in item_name.lower():
                            src = "/images/items/Pack Hourglass.webp"
                            alt = "Pack Hourglass"
                        else:
                            image_url = item.get('image_url', '')
                            filename = image_url.split('/')[-1] if image_url else ''
                            src = f"/images/items/{filename}"
                            alt = item.get('name', 'Item')
                        row_data.append({'type': item_type, 'src': src, 'alt': alt})
                rows.append(row_data)
            patterns[str(idx)] = {'rows': rows}
    return patterns

def generate_featured_cards(promo_cards):
    """目玉カードのHTMLを生成"""
    if not promo_cards:
        return '      <!-- No promo cards -->'
    
    html_lines = []
    for card in promo_cards:
        # カード名をアンダースコア区切り、先頭大文字に変換
        card_name_underscore = card['name'].replace(' Rare', '').replace(' ', '_')
        
        # URLを生成
        card_id = card['id']
        card_url = f"/cards/{card_id}/{card_name_underscore}.html"
        
        # alt属性用の名前（スペースをアンダースコアに変換）
        alt_name = card['name'].replace(' ', '_').replace('Rare', '').strip()
        
        html_lines.append(f'''      <a href="{card_url}">
        <img src="/images/cards/{card['id']}.webp" alt="{alt_name}" class="featured-card">
      </a>''')
    
    return '\n'.join(html_lines)

def get_currency_image(currency_name):
    currency_lower = currency_name.lower()
    if 'premium ticket' in currency_lower:
        return '/images/items/Premium Ticket.webp'
    elif 'event shop ticket' in currency_lower:
        return f"/images/tickets/{currency_name}.webp"
    elif 'promo card exchange ticket' in currency_lower:
        return f"/images/tickets/{currency_name}.webp"
    else:
        return '/images/items/Placeholder.webp'

def generate_accessory_filename(item_name):
    if '(' in item_name:
        theme = item_name.split('(')[0].strip()
    else:
        if 'shinedust' in item_name.lower():
            return 'items/Shinedust.webp'
        theme = item_name.strip()
    
    name_lower = item_name.lower()
    theme = theme.replace('&', 'and').replace(' ', '_')
    
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
    elif 'icon' in name_lower:
        return f"icons/{theme}_icon.webp"
    else:
        return f"other/{theme}.webp"

def generate_accessory_items(items):
    def get_order(item_name):
        name_lower = item_name.lower()
        if 'pokémon coin' in name_lower or 'coin' in name_lower:
            return 1
        elif 'playmat' in name_lower:
            return 2
        elif 'card sleeve' in name_lower:
            return 3
        elif 'backdrop' in name_lower:
            return 4
        elif 'cover' in name_lower:
            return 5
        elif 'icon' in name_lower:
            return 6
        return 999
    
    accessory_items = [item for item in items if 'shinedust' not in item['name'].lower()]
    sorted_items = sorted(accessory_items, key=lambda x: get_order(x['name']))
    shinedust_items = [item for item in items if 'shinedust' in item['name'].lower()]
    
    html_lines = []
    for item in sorted_items:
        img_path = generate_accessory_filename(item['name'])
        description = item.get('description', item['name'])
        currency = item.get('currency', 'Event Shop Ticket')
        currency_img = get_currency_image(currency)
        
        html_lines.append(f'''          <div class="item tooltip">
            <img src="/images/accessories/{img_path}" alt="{item['name']}">
            <span class="tooltiptext">{description}</span>
            <div class="Event-Shop-Ticket">
              <img src="{currency_img}" alt="{currency}">
              <span>{item['price']}</span>
            </div>
          </div>''')
    
    for item in shinedust_items:
        amount = extract_shinedust_amount(item['name'])
        currency = item.get('currency', 'Event Shop Ticket')
        currency_img = get_currency_image(currency)
        html_lines.append(f'''          <div class="item tooltip">
            <img src="/images/items/Shinedust.webp" alt="Shinedust">
            <span class="tooltiptext">Shinedust×{amount}</span>
            <div class="Event-Shop-Ticket">
              <img src="{currency_img}" alt="{currency}">
              <span>{item['price']}</span>
            </div>
          </div>''')
    
    return '\n'.join(html_lines)

def generate_card_exchange_items(items, promo_cards):
    """カード交換アイテムのHTMLを生成（ツールチップなし）"""
    if not items:
        return ''
    
    html_lines = []
    for item in items:
        card_name = item['name']
        
        # プロモカードのIDを探す
        card_id = None
        for promo in promo_cards:
            if promo['name'].replace(' Rare', '') == card_name:
                card_id = promo['id']
                break
        
        if not card_id:
            continue
        
        card_name_underscore = card_name.replace(' ', '_')
        card_url = f"/cards/{card_id}/{card_name_underscore}.html"
        
        # tooltip クラスを削除
        html_lines.append(f'''          <div class="item">
            <a href="{card_url}">
              <img src="/images/cards/{card_id}.webp" alt="{card_name}">
            </a>
            <div class="Event-Shop-Ticket">
              <img src="{get_currency_image(item['currency'])}" alt="{item['currency']}">
              <span>{item['price']}</span>
            </div>
          </div>''')
    
    return '\n'.join(html_lines)

def get_reward_image_info(reward, promo_cards):
    reward_name = reward['name'].lower()
    amount = reward.get('amount', '1')
    clean_name = re.sub(r'^\d+x\s*', '', reward['name'])
    
    img_path = '/images/items/Placeholder.webp'
    alt = clean_name
    
    if 'premium ticket' in reward_name:
        img_path = '/images/items/Premium Ticket.webp'
        alt = 'Premium Ticket'
    elif 'event shop ticket' in reward_name:
        img_path = f"/images/tickets/{clean_name}.webp"
        alt = clean_name
    elif 'promo card exchange ticket' in reward_name:
        img_path = f"/images/tickets/{clean_name}.webp"
        alt = clean_name
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
        for promo in promo_cards:
            if promo['name'].lower() in reward_name:
                img_path = f"/images/cards/{promo['id']}.webp"
                alt = promo['name']
                break
    
    return img_path, alt, amount

def generate_mission_cards(missions, promo_cards):
    html_lines = []
    for i, mission in enumerate(missions, 1):
        description = mission['description']
        rewards = mission.get('rewards', [])
        
        preview_items = []
        for reward in rewards:
            img_path, alt, amount = get_reward_image_info(reward, promo_cards)
            preview_items.append(f'''                  <div class="mission-card__preview-item">
                    <img src="{img_path}" alt="{alt}">
                    <span>×{amount}</span>
                  </div>''')
        
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

def generate_mission_sections(mission_sections, mission_intro_text):
    """複数のミッションセクションのHTMLを生成"""
    if not mission_sections:
        return ''
    sections_html = []
    for idx, section in enumerate(mission_sections, 1):
        if idx == 1:
            intro_text = mission_intro_text
        else:
            intro_text = f"""Event Missions (Part {idx})<br>
The second batch of Event Missions is now available.<br>
Complete these limited-time missions to earn Event Shop Tickets and exchange them for exclusive accessories in the Event Shop."""
        
        sections_html.append(f'''
    <!-- {section['title']} -->
    <div class="section">
      <div class="content">
    
        <div class="subheading">
          <h2>{section['title']}</h2>
        </div>
        
        <!-- 開催期間 -->
        <div class="event-row">
          <div class="label">Event period</div>
          <div class="date">{section['period']}</div>
        </div>
        
        <!-- 説明文 -->
        <div class="intro">
          <p>
            {intro_text}
          </p>
        </div>
    
        <!-- ミッション一覧 -->
        <div class="mission-group">
          <div class="mission-list">
{section['html']}
          </div>
        </div>

      </div>
    </div>''')
    return '\n'.join(sections_html)
    
def generate_wonder_pick_html(json_data, json_filepath):
    """ワンダーピックイベントのHTMLを生成"""
    # 基本情報の取得
    title = json_data['title']
    period_text = json_data['period']['text']
    start_date = json_data['period']['start_date']
    year = start_date.split('-')[0]
    main_period_text = f"{period_text}, {year}"
    
    promo_cards = json_data.get('promo_cards', [])
    bonus_patterns = generate_bonus_patterns(json_data.get('bonus_picks', []))
    chansey_patterns = generate_chansey_patterns(json_data.get('rare_picks', []))
    
    # ボタンのHTMLを生成
    bonus_buttons = generate_pattern_buttons(len(bonus_patterns))
    chansey_buttons = generate_pattern_buttons(len(chansey_patterns))
    
    # ショップアイテム情報の取得（アクセサリーとカードを分離）
    accessory_items = []
    card_items = []
    for shop_section in json_data.get('shop_items', []):
        if 'items' in shop_section:
            title_text = shop_section.get('title', '')
            # Exchange または Card を含む場合はカード交換用
            
            if 'Card' in title_text:
                card_items.extend(shop_section['items'])
            else:
                accessory_items.extend(shop_section['items'])
    
    # アクセサリーアイテムのHTML生成（あれば）
    accessory_html = ''
    if accessory_items:
        accessory_html = generate_accessory_items(accessory_items)
    
    # カード交換アイテムのHTML生成（あれば）
    card_exchange_html = generate_card_exchange_items(card_items, promo_cards)
    
    # 説明文の選択（promo_reissueフラグがある場合は専用文章）
    is_promo_reissue = json_data.get('promo_reissue', False)
    
    if is_promo_reissue:
        intro_text = """This event gives you another chance to obtain promotional cards from previous Wonder Pick events.

All cards released in the A Series Wonder Pick events are available again for a limited time.

During the event, you can try the free Bonus Pick, where you can earn valuable rewards such as Shop Tickets and Wonder Hourglasses. In addition, the Chansey Pick offers a chance to obtain these past promotional cards.

You can also use tickets earned by completing missions to redeem one card of your choice from the full lineup of 24 Promo A cards available during the event."""
        
        wonder_pick_intro_text = "During the event period, 'Chansey' and 'Bonus Pick' will appear in the Get Challenge. By clearing these challenges, you can obtain event-exclusive promo cards from previous Wonder Pick events."
        
        # 復刻イベント用のミッション説明文
        mission_intro_text = "Event Missions are special missions available during the event period. Completing these missions rewards Event Shop Tickets that can be used to exchange for promo cards in the Card Exchange section."
    else:
        # 通常の説明文
        if accessory_items:
            intro_text = f"A new Wonder Pick event is now live. Players can obtain Promo cards—{get_promo_card_names(promo_cards)}—through Bonus Picks and Chansey Picks.\n\nIn addition, new themed accessories have been added to the shop. These items can be exchanged using Event Shop Tickets, which can be earned by completing event missions and participating in Bonus Picks.\n\nDon't miss this limited-time opportunity to collect exclusive promo cards and special accessories."
        else:
            intro_text = f"A new Wonder Pick event is now live. Players can obtain Promo cards—{get_promo_card_names(promo_cards)}—through Bonus Picks and Chansey Picks.\n\nDon't miss this limited-time opportunity to collect exclusive promo cards."
        
        wonder_pick_intro_text = f"During the event period, 'Chansey' and 'Bonus Pick' will appear in the Get Challenge. By clearing these challenges, you can obtain the event-exclusive promo cards <strong>{get_promo_card_names(promo_cards)}</strong>."
        
        # 通常イベント用のミッション説明文
        mission_intro_text = "Event Missions are special missions available during the event period. Completing these missions rewards Event Shop Tickets that can be used to purchase accessories in the Event Shop."
    
    # ミッション
    missions_list = json_data.get('missions', [])
    all_mission_html = []
    for idx, mission_set in enumerate(missions_list, 1):
        missions = mission_set.get('missions', [])
        if missions:
            mission_html = generate_mission_cards(missions, promo_cards)
            section_title = "Event Missions" if len(missions_list) == 1 else f"Event Missions Part {idx}"
            all_mission_html.append({
                'title': section_title,
                'period': mission_set.get('period', ''),
                'html': mission_html
            })
    
    hero_image_name = f"{title}.webp"
    output_filename = f"{title}.html"
    output_filepath = Path(json_filepath).parent / output_filename
    
    featured_cards_html = generate_featured_cards(promo_cards)
    mission_sections_html = generate_mission_sections(all_mission_html, mission_intro_text)
    
    bonus_patterns_json = json.dumps(bonus_patterns, ensure_ascii=False)
    chansey_patterns_json = json.dumps(chansey_patterns, ensure_ascii=False)
    
    # カード交換セクションの有無でHTMLを分岐
    card_section_html = ''
    if card_exchange_html:
        card_section_html = f'''
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Card Exchange</h2></div>
        <div class="event-row"><div class="label">Event period</div><div class="date">{main_period_text}</div></div>
        <div class="accessory-grid">{card_exchange_html}</div>
        <div class="intro"><p>Exchange your Event Shop Tickets for these promo cards.</p></div>
      </div>
    </div>'''
    
    # アクセサリーセクションの有無でHTMLを分岐
    accessory_section_html = ''
    if accessory_html:
        accessory_section_html = f'''
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Event Shop Accessories</h2></div>
        <div class="event-row"><div class="label">Event period</div><div class="date">{main_period_text}</div></div>
        <div class="accessory-grid">{accessory_html}</div>
        <div class="intro"><p>Available only during the event period.</p></div>
      </div>
    </div>'''
    
    # intro_textを段落に分割
    intro_paragraphs = intro_text.split('\n\n')
    intro_html = '\n'.join([f'<p>{p.replace(chr(10), " ")}</p>' for p in intro_paragraphs if p.strip()])
    
    html_template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/base.css">
  <link rel="stylesheet" href="/styles/tooltip.css">
  <link rel="stylesheet" href="/styles/wonder_pick.css">
</head>
<body class="page-body">
  <div id="header"></div>
  <nav class="breadcrumbs">
    <a href="/">Home</a>
    <a href="/Events.html">Events</a>
    <a href="/events/wonder_pick/{output_filename}">{title}</a>
  </nav>
  <main class="page-main">
    <div class="section">
      <h1 class="main-title">{title}</h1>
    </div>
    <img src="/images/events/wonder_pick/{hero_image_name}" alt="{title}" class="hero_image">
    <div class="event-row">
      <div class="label">Event period</div>
      <div class="date">{main_period_text}</div>
    </div>
    <div class="intro">
      {intro_html}
    </div>
    <div class="featured-wonder_pick">
{featured_cards_html}
    </div>
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Wonder Pick</h2></div>
        <div class="event-row"><div class="label">Event period</div><div class="date">{main_period_text}</div></div>
        <div class="intro">
          <p>{wonder_pick_intro_text}</p>
          <p>The timing of challenge appearances varies by user and occurs completely at random. Therefore, we recommend that you <strong>regularly open the app during the event period to check if challenges have appeared</strong>.</p>
        </div>
        <div class="bonus-pick" data-wp-switcher data-wp-default="1" data-wp-show-cost="true" data-wp-patterns='{bonus_patterns_json}'>
          <div data-wp-buttons class="pattern-button">
            {bonus_buttons}
          </div>
          <div class="bonus-pick_outer"><div class="bonus-pick_inner"><img src="/images/icon/bonus-pick_icon.webp" alt="Bonus Pick Icon" class="bonus-pick_image"><span class="bonus-pick_label">Bonus Pick</span></div></div>
          <div data-wp-content class="bonus-pick_content"></div>
          <div class="bonus-pick_intro"><p>Free Challenges can be attempted without consuming any Challenge Power. Be sure to take them on whenever you see them.</p></div>
        </div>
        <div class="bonus-pick" data-wp-switcher data-wp-type="chansey" data-wp-default="1" data-wp-patterns='{chansey_patterns_json}'>
          <div data-wp-buttons class="pattern-button">
            {chansey_buttons}
          </div>
          <div class="chansey-pick_outer"><div class="chansey-pick_inner"><img src="/images/icon/chansey-pick_icon.webp" alt="Chansey Pick Icon" class="chansey-pick_image"><span class="bonus-pick_label">Chansey Pick</span></div></div>
          <div data-wp-content class="chansey-pick_content"></div>
          <div class="bonus-pick_intro"><p>Use 2 Wonder Stamina to attempt the Chansey Pick. Save 2 during the event so you're always ready when it appears.</p></div>
        </div>
      </div>
    </div>
{accessory_section_html}
{card_section_html}
{mission_sections_html}
  </main>
  <div id="footer"></div>
  <script src="/js/header-footer-load.js"></script>
  <script src="/js/wonder-pick-switcher.js"></script>
  <script src="/js/tooltip.js"></script>
</body>
</html>'''
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"  ✅ 生成完了: {output_filename}")
    return output_filepath

def main():
    print("=== ワンダーピックイベント一括HTML生成ツール ===")
    print("フォルダを選択すると、中のすべてのJSONファイルをHTMLに変換します\n")
    folder_path = select_folder()
    if not folder_path:
        print("フォルダが選択されませんでした。")
        return
    print(f"選択されたフォルダ: {folder_path}")
    json_files = find_json_files(folder_path)
    if not json_files:
        print("フォルダ内にJSONファイルが見つかりませんでした。")
        messagebox.showwarning("警告", "選択されたフォルダ内にJSONファイルが見つかりませんでした。")
        return
    print(f"\n📁 {len(json_files)}個のJSONファイルが見つかりました。")
    successful, failed = [], []
    for i, json_file in enumerate(json_files, 1):
        print(f"\n--- 処理中 {i}/{len(json_files)} ---")
        try:
            json_data = load_json_data(json_file)
            output_filepath = generate_wonder_pick_html(json_data, json_file)
            successful.append(str(output_filepath))
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            failed.append(str(json_file))
    print("\n" + "="*50)
    print(f"✅ 処理完了: {len(successful)}個成功")
    if failed:
        print(f"❌ 失敗: {len(failed)}個")
        for f in failed:
            print(f"  - {f}")
    root = tk.Tk()
    root.withdraw()
    if failed:
        messagebox.showwarning("処理完了（一部エラー）", f"HTML生成が完了しました。\n\n✅ 成功: {len(successful)}個\n❌ 失敗: {len(failed)}個")
    else:
        messagebox.showinfo("完了", f"すべてのJSONファイルのHTML生成が完了しました！\n\n✅ 変換したファイル数: {len(successful)}個")
    root.destroy()

if __name__ == "__main__":
    main()