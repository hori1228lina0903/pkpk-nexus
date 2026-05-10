import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re

# JSONファイルの場所からの相対パスで出力先を指定
OUTPUT_RELATIVE_PATH = "../../../events/drop_event"

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

def strip_html(text):
    return re.sub('<[^<]+?>', '', text)

def get_card_image_path(card_name, card_url):
    match = re.search(r'/cards/[^/]+/(\d+)/', card_url)
    if match:
        card_id = match.group(1)
        return f"/images/cards/{card_id}.webp"
    name_underscore = card_name.lower().replace(' ', '_').replace("'", "")
    return f"/images/cards/promo/{name_underscore}.webp"

def generate_promo_cards_html(promo_pack):
    cards = promo_pack.get('cards', [])
    if not cards:
        return '      <!-- No promo cards -->'
    
    html_lines = []
    for card in cards:
        card_name = card['name']
        card_url = card['url']
        img_path = get_card_image_path(card_name, card_url)
        card_name_underscore = card_name.lower().replace(' ', '_').replace("'", "")
        
        html_lines.append(f'''      <a href="{card_url}">
        <img src="{img_path}" alt="{card_name_underscore}" class="featured-card">
      </a>''')
    
    return '\n'.join(html_lines)

def generate_battle_tasks_html(tasks):
    if not tasks:
        return '<p class="no-tasks">No tasks available</p>'
    
    task_items = []
    for task in tasks:
        task_items.append(f'<li>{task}</li>')
    
    return f'<ul class="battle-tasks">\n{"".join(task_items)}\n</ul>'

def generate_battles_html(battles):
    if not battles:
        return ''
    
    html_lines = []
    for i, battle in enumerate(battles, 1):
        difficulty = battle.get('difficulty', 'Unknown')
        deck_type = battle.get('deck_type', 'Unknown')
        tasks = battle.get('tasks', [])
        difficulty_class = difficulty.lower()
        
        html_lines.append(f'''
    <!-- Battle {i}: {difficulty} -->
    <div class="battle-card {difficulty_class}">
      <div class="battle-card__header">
        <span class="difficulty-badge {difficulty_class}">{difficulty}</span>
        <span class="deck-type">Deck: {deck_type}</span>
      </div>
      <div class="battle-card__tasks">
        <h3>Tasks</h3>
        {generate_battle_tasks_html(tasks)}
      </div>
    </div>''')
    
    return '\n'.join(html_lines)

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', '_', title).replace(' ', '_')

def generate_drop_event_html(json_data, json_filepath):
    """ドロップイベントのHTMLを生成"""
    title = json_data['title']
    period_text = json_data['period']['text']
    start_date = json_data['period']['start_date']
    year = start_date.split('-')[0]
    main_period_text = f"{period_text}, {year}"
    
    promo_pack = json_data.get('promo_pack', {})
    promo_pack_name = promo_pack.get('name', '')
    battles = json_data.get('battles', [])
    
    promo_cards_html = generate_promo_cards_html(promo_pack)
    battles_html = generate_battles_html(battles)
    
    hero_image_name = f"{sanitize_filename(title)}.webp"
    output_filename = f"{sanitize_filename(title)}.html"
    
    # JSONファイルの場所から相対パスで出力先を決定
    json_dir = Path(json_filepath).parent
    output_dir = (json_dir / OUTPUT_RELATIVE_PATH).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filepath = output_dir / output_filename
    
    print(f"   JSON場所: {json_dir}")
    print(f"   出力先: {output_dir}")
    
    promo_pack_section = ''
    if promo_pack_name or promo_pack.get('cards'):
        promo_pack_section = f'''
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Promo Pack</h2></div>
        <div class="event-row"><div class="label">Pack name</div><div class="date">{promo_pack_name or "Promo Pack"}</div></div>
        <div class="featured-cards">
{promo_cards_html}
        </div>
        <div class="intro"><p>These promo cards can be obtained as rewards from event battles.</p></div>
      </div>
    </div>'''
    
    battles_section = ''
    if battles_html:
        battles_section = f'''
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Event Battles</h2></div>
        <div class="event-row"><div class="label">Event period</div><div class="date">{main_period_text}</div></div>
        <div class="intro"><p>Clear battles to earn rewards. Higher difficulties offer better rewards.</p></div>
        <div class="battles-grid">
{battles_html}
        </div>
      </div>
    </div>'''
    
    intro_text = f"""The {title} is a limited-time solo battle event.
During the event period, you can challenge special battles to obtain promo cards and other rewards.
Complete all tasks in each battle to earn bonus rewards!"""
    
    intro_paragraphs = intro_text.split('\n\n')
    intro_html = '\n'.join([f'<p>{p.replace(chr(10), " ")}</p>' for p in intro_paragraphs if p.strip()])
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/base.css">
  <link rel="stylesheet" href="/styles/drop_event.css">
</head>
<body class="page-body">
  <div id="header"></div>
  <nav class="breadcrumbs">
    <a href="/">Home</a>
    <a href="/Events.html">Events</a>
    <a href="/events/drop_event/{output_filename}">{title}</a>
  </nav>
  <main class="page-main">
    <div class="section">
      <h1 class="main-title">{title}</h1>
    </div>
    <img src="/images/events/drop_event/{hero_image_name}" alt="{title}" class="hero_image">
    <div class="event-row">
      <div class="label">Event period</div>
      <div class="date">{main_period_text}</div>
    </div>
    <div class="intro">
      {intro_html}
    </div>
{promo_pack_section}
{battles_section}
  </main>
  <div id="footer"></div>
  <script src="/js/header-footer-load.js"></script>
</body>
</html>'''
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"  ✅ 生成完了: {output_filename} -> {output_filepath}")
    return output_filepath

def main():
    print("=== ドロップイベント一括HTML生成ツール ===")
    print(f"📂 出力先（JSONからの相対パス）: {OUTPUT_RELATIVE_PATH}")
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
        print(f"   ファイル: {json_file.name}")
        try:
            json_data = load_json_data(json_file)
            output_filepath = generate_drop_event_html(json_data, json_file)
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