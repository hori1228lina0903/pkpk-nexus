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

def generate_rank_html(json_data, json_filepath):
    """ランクマッチイベントのHTMLを生成"""
    title = json_data['title']
    period_text = json_data['period']['text']
    start_date = json_data['period']['start_date']
    year = start_date.split('-')[0]
    main_period_text = f"{period_text}, {year}"
    set_name = json_data.get('set_name', '')
    ranks = json_data.get('ranks', [])
    
    # ランクバッジの設定マップ（パスと拡張子を統一）
    rank_badge_map = {
        "Beginner": "beginner",
        "Poké Ball": "poke_ball",
        "Great Ball": "great_ball",
        "Ultra Ball": "ultra_ball",
        "Master Ball": "master_ball"
    }
    
    current_category = ""
    rank_tables_html = []
    table_rows = []
    
    for rank in ranks:
        category = rank.get('category', '')
        rank_name = rank.get('rank', '')
        emblem = rank.get('emblem')
        reward = rank.get('reward')
        
        # カテゴリが変わったらテーブルを閉じて新しいテーブルを開始
        if category != current_category:
            if table_rows:
                # ランク帯の画像タグを生成
                badge_key = rank_badge_map.get(current_category, "")
                rank_badge_img = f'<img src="/images/icon/{badge_key}.webp" alt="{current_category}" class="rank-badge">' if badge_key else ""
                
                rank_tables_html.append(f'''
    <div class="rank-section">
      <div class="rank-header">
        {rank_badge_img}
        <h3>{current_category}</h3>
      </div>
      <table class="rank-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Reward</th>
          </tr>
        </thead>
        <tbody>
{''.join(table_rows)}
        </tbody>
      </table>
    </div>''')
                table_rows = []
            current_category = category
        
        # ヘッダー行はスキップ
        if rank_name == "Rank" and not emblem:
            continue
        
        # 報酬のHTML
        reward_html = ""
        if emblem or reward:
            reward_items = []
            
            # エンブレム（ツールチップ付き）
            if emblem:
                emblem_name = emblem.get('name', '')
                local_file = emblem.get('local_file', '')
                reward_items.append(f'''            <div class="reward-emblem tooltip">
              <img src="/images/emblem/{local_file}" alt="{emblem_name}" class="reward-icon">
              <span class="tooltiptext">{emblem_name}</span>
            </div>''')
            
            # 砂時計報酬
            if reward:
                amount = reward.get('amount', '')
                reward_items.append(f'''            <div class="reward-hourglass">
              <img src="/images/items/Pack Hourglass.webp" alt="Pack Hourglass" class="reward-icon">
              <span class="reward-amount">×{amount}</span>
            </div>''')
            
            reward_html = f'''          <td class="reward-cell">
            <div class="reward-content">
{chr(10).join(reward_items)}
            </div>
            </td>'''
        else:
            reward_html = '            <td></td>'
        
        # テーブル行を追加
        table_rows.append(f'''            <tr>
          <td class="rank-cell">{rank_name}</td>
{reward_html}
            </tr>
''')
    
    # 最後のテーブルを追加
    if table_rows:
        badge_key = rank_badge_map.get(current_category, "")
        rank_badge_img = f'<img src="/images/icon/{badge_key}.webp" alt="{current_category}" class="rank-badge">' if badge_key else ""
        
        rank_tables_html.append(f'''
    <div class="rank-section">
      <div class="rank-header">
        {rank_badge_img}
        <h3>{current_category}</h3>
      </div>
      <table class="rank-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Reward</th>
          </tr>
        </thead>
        <tbody>
{''.join(table_rows)}
        </tbody>
      </table>
    </div>''')
    
    rank_tables_content = '\n'.join(rank_tables_html)
    
    # 説明文
    intro_text = f"""<p><strong>Ranked Match Season {set_name}</strong> is now live! Battle against other players to climb the ranks and earn exclusive emblems and rewards.</p>

<p>The season runs from <strong>{main_period_text}</strong>. At the end of the season, rewards will be distributed based on your highest achieved rank. Be sure to participate and claim your rewards before the season ends!</p>"""
    
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
  <link rel="stylesheet" href="/styles/ranked_match.css">
</head>
<body class="page-body">
  <div id="header"></div>
  <nav class="breadcrumbs">
    <a href="/">Home</a>
    <a href="/Events.html">Events</a>
    <a href="/events/ranked_match/{output_filename}">{title}</a>
  </nav>
  <main class="page-main">
    <div class="section">
      <h1 class="main-title">{title}</h1>
    </div>
    <img src="/images/events/ranked_match/{hero_image_name}" alt="{title}" class="hero_image">
    <div class="event-row">
      <div class="label">Event period</div>
      <div class="date">{main_period_text}</div>
    </div>
    <div class="intro">
      {intro_text}
    </div>
    
    <div class="section">
      <div class="content">
        <div class="subheading"><h2>Rank Rewards</h2></div>
        <div class="intro">
          <p>Rewards are distributed based on the highest rank achieved during the season. Earn exclusive emblems and Pack Hourglasses by climbing the ranks!</p>
        </div>
        <div class="rank-rewards">
{rank_tables_content}
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
    print("=== ランクマッチイベントHTML生成ツール ===")
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
            output_filepath = generate_rank_html(json_data, json_file)
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