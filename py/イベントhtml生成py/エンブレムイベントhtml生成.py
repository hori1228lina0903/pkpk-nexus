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

def generate_emblem_html(json_data, json_filepath):
    """エンブレムイベントのHTMLを生成"""
    title = json_data['title']
    period_text = json_data['period']['text']
    start_date = json_data['period']['start_date']
    year = start_date.split('-')[0]
    main_period_text = f"{period_text}, {year}"
    emblems = json_data.get('emblems', [])
    missions = json_data.get('missions', [])
    
    # ★★★ エンブレム獲得条件に "in a row" が含まれているか判定 ★★★
    is_consecutive_event = False
    for emblem in emblems:
        condition = emblem.get('condition', '')
        if 'in a row' in condition.lower():
            is_consecutive_event = True
            break
    
    # エンブレムカードのHTMLを生成
    emblems_html = ""
    if emblems:
        emblem_cards = []
        for emblem in emblems:
            emblem_name = emblem.get('name', '')
            local_file = emblem.get('local_file', '')
            condition = emblem.get('condition', '')
            
            # conditionを加工（例: "Gold emblem Winning 9 versus battle" → "Winning 9 versus battle"）
            if condition:
                condition = re.sub(r'^[A-Za-z]+\s+emblem\s+', '', condition)
            else:
                condition = "Complete event missions"
            
            emblem_cards.append(f'''            <div class="emblem-card">
              <div class="emblem-card__inner">
                <div class="emblem-card__preview">
                  <div class="emblem-icon tooltip">
                    <img src="/images/emblem/{local_file}" alt="{emblem_name}" class="emblem-img">
                    <span class="tooltiptext">{emblem_name}</span>
                  </div>
                </div>
                <div class="emblem-card__content">
                  <div class="emblem-card__condition">{condition}</div>
                </div>
              </div>
            </div>''')
        
        emblems_html = f'''
    <div class="emblems-list">
{chr(10).join(emblem_cards)}
    </div>'''
    
    # ミッションのHTMLを生成
    missions_html = ""
    if missions:
        mission_cards = []
        for mission_set in missions:
            mission_list = mission_set.get('missions', [])
            
            for mission in mission_list:
                description = mission.get('description', '')
                reward = mission.get('reward', {})
                
                reward_html = ""
                if reward:
                    reward_name = reward.get('name', '')
                    amount = reward.get('amount', '')
                    
                    reward_lower = reward_name.lower()
                    if 'pack hourglass' in reward_lower:
                        img_src = "/images/items/Pack Hourglass.webp"
                    elif 'wonder hourglass' in reward_lower:
                        img_src = "/images/items/Wonder Hourglass.webp"
                    elif 'premium ticket' in reward_lower:
                        img_src = "/images/items/Premium Ticket.webp"
                    elif 'trade token' in reward_lower:
                        img_src = "/images/items/Trade Tokens.webp"
                    elif 'shinedust' in reward_lower:
                        img_src = "/images/items/Shinedust.webp"
                    else:
                        img_src = "/images/items/Placeholder.webp"
                    
                    reward_html = f'''                  <div class="mission-card__preview-item">
                    <img src="{img_src}" alt="{reward_name}">
                    <span>×{amount}</span>
                  </div>'''
                
                mission_cards.append(f'''            <div class="mission-card">
              <div class="mission-card__inner">
                <div class="mission-card__preview">
                  {reward_html}
                </div>
                <div class="mission-card__content">
                  <div class="mission-card__text">{description}</div>
                </div>
              </div>
            </div>''')
        
        missions_html = f'''
    <div class="mission-list">
{chr(10).join(mission_cards)}
    </div>'''
    
    # 説明文
    intro_text = f"""<p><strong>{title}</strong> is now live! Complete event missions to earn exclusive emblems.</p>

<p>The event runs from <strong>{main_period_text}</strong>. Don't miss this limited-time opportunity to collect these special emblems!</p>"""
    
    # ★★★ 連勝イベントかどうかでエンブレム説明文を切り替え ★★★
    if is_consecutive_event:
        emblem_intro_text = "Earn these emblems by achieving a certain number of consecutive wins in versus battles."
    else:
        emblem_intro_text = "Earn these emblems by achieving a certain number of wins in versus battles."
    
    hero_image_name = f"{title}.webp"
    output_filename = f"{title}.html"
    output_filepath = Path(json_filepath).parent / output_filename
    
    html_template = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/base.css">
  <link rel="stylesheet" href="/styles/tooltip.css">
  <link rel="stylesheet" href="/styles/emblem_event.css">
</head>
<body class="page-body">
  <div id="header"></div>
  <nav class="breadcrumbs">
    <a href="/">Home</a>
    <a href="/Events.html">Events</a>
    <a href="/events/emblem_event/{output_filename}">{title}</a>
  </nav>
  <main class="page-main">
    <div class="section">
      <h1 class="main-title">{title}</h1>
    </div>
    <img src="/images/events/emblem_event/{hero_image_name}" alt="{title}" class="hero_image">
    <div class="event-row">
      <div class="label">Event period</div>
      <div class="date">{main_period_text}</div>
    </div>
    <div class="intro">
      {intro_text}
    </div>
    
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Event Emblems</h2></div>
        <div class="intro">
          <p>{emblem_intro_text}</p>
        </div>
        <div class="emblems-container">
{emblems_html}
        </div>
      </div>
    </div>
    
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Event Missions</h2></div>
        <div class="event-row"><div class="label">Event period</div><div class="date">{main_period_text}</div></div>
        <div class="intro">
          <p>During the event period, special missions will appear. Complete these missions to earn valuable rewards such as Pack Hourglasses and Shinedust!</p>
        </div>
        <div class="missions-container">
{missions_html}
        </div>
      </div>
    </div>
  </main>
  <div id="footer"></div>
  <script src="/js/header-footer-load.js"></script>
  <script src="/js/tooltip.js"></script>
</body>
</html>'''
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"  ✅ 生成完了: {output_filename}")
    return output_filepath

def main():
    print("=== エンブレムイベントHTML生成ツール ===")
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
            output_filepath = generate_emblem_html(json_data, json_file)
            successful.append(str(output_filepath))
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            import traceback
            traceback.print_exc()
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