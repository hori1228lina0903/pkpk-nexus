import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from collections import OrderedDict
import re
import threading  # 画面フリーズ防止用

# エネルギータイプ → アイコン画像
energy_icon_map = {
    "grass": "/images/energy/grass.webp",
    "fire": "/images/energy/fire.webp",
    "water": "/images/energy/water.webp",
    "lightning": "/images/energy/lightning.webp",
    "psychic": "/images/energy/psychic.webp",
    "fighting": "/images/energy/fighting.webp",
    "darkness": "/images/energy/darkness.webp",
    "metal": "/images/energy/metal.webp",
    "fairy": "/images/energy/fairy.webp",
    "dragon": "/images/energy/dragon.webp",
    "colorless": "/images/energy/colorless.webp",
}

def load_pack_set_info():
    try:
        pack_set_path = "data/pack_set_name.json"
        with open(pack_set_path, "r", encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except Exception:
        return OrderedDict()

def convert_to_image_filename(text):
    if not text: return ""
    filename = text.replace(":", "")
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename

def generate_rarity_icons(rarity_data):
    icons = ""
    if isinstance(rarity_data, dict) and "rarity_types" in rarity_data:
        for r_type in rarity_data["rarity_types"]:
            for _ in range(rarity_data.get("count", 1)):
                icons += f'<img src="/images/rarities/{r_type}.webp" class="rarity-icon">'
    return icons or "なし"

def generate_card_number_html(card_numbers):
    if not card_numbers: return ""
    if isinstance(card_numbers, str): card_numbers = [card_numbers]
    html = '<div class="sets-wrapper"><div class="sets-inner-scroll">'
    for cn in card_numbers:
        if "#" in cn:
            set_code, num = cn.split("#", 1)
            html += f'<div class="card-number-item"><span class="card-set-code">{set_code}</span><span>{num}</span></div>'
        else:
            html += f'<div class="card-number-item"><span>{cn}</span></div>'
    html += '</div></div>'
    return html

def generate_weakness_html(weakness_text):
    if not weakness_text or weakness_text == "None":
        return "None"
    for e_type in energy_icon_map.keys():
        if e_type in weakness_text.lower():
            icon_url = energy_icon_map[e_type]
            suffix = weakness_text.lower().split(e_type)[-1].strip()
            return f'<img src="{icon_url}" class="energy-icon"> {e_type} {suffix}'
    return weakness_text

def generate_sets_info(data, pack_set_info):
    if "収録セット" not in data or not data["収録セット"]: return ""
    html = '<tr><th>Sets</th><td><div class="sets-wrapper"><div class="sets-inner-scroll">'
    displayed_sets = []
    for _, info in pack_set_info.items():
        set_name_in_json = info.get("set", "")
        set_name_json_conv = convert_to_image_filename(set_name_in_json)
        for s_name in data["収録セット"]:
            s_name_conv = convert_to_image_filename(s_name)
            if s_name_conv == set_name_json_conv and s_name not in displayed_sets:
                img = convert_to_image_filename(s_name)
                html += f'<div class="set-item"><img src="/images/packs/{img}.webp" class="pack-image"><div class="set-name">{s_name}</div></div>'
                displayed_sets.append(s_name)
    for s_name in data["収録セット"]:
        if s_name not in displayed_sets:
            img = convert_to_image_filename(s_name)
            html += f'<div class="set-item"><img src="/images/packs/{img}.webp" class="pack-image"><div class="set-name">{s_name}</div></div>'
    html += '</div></div></td></tr>'
    return html

def generate_packs_info(data, pack_set_info):
    if "入手方法" not in data: return ""
    pack_items = [m.split(":", 1)[1].strip() for m in data["入手方法"] if m.startswith("パック:")]
    if not pack_items: return ""
    html = '<tr><th>Pack</th><td><div class="sets-wrapper"><div class="sets-inner-scroll">'
    displayed_packs = []
    for _, info in pack_set_info.items():
        packs_in_json = info.get("packs", [])
        for p_json_name in packs_in_json:
            p_json_conv = convert_to_image_filename(p_json_name)
            for p_name in pack_items:
                p_name_conv = convert_to_image_filename(p_name)
                if p_name_conv == p_json_conv and p_name not in displayed_packs:
                    img = convert_to_image_filename(p_name)
                    html += f'<div class="set-item"><img src="/images/packs/{img}.webp" class="pack-image"><div class="set-name">{p_name}</div></div>'
                    displayed_packs.append(p_name)
    for p_name in pack_items:
        if p_name not in displayed_packs:
            img = convert_to_image_filename(p_name)
            html += f'<div class="set-item"><img src="/images/packs/{img}.webp" class="pack-image"><div class="set-name">{p_name}</div></div>'
    html += '</div></div></td></tr>'
    return html

def generate_how_to_get(data):
    if "入手方法" not in data: return "No Information"
    methods = []
    for m in data["入手方法"]:
        if m.startswith("パック:"): continue
        
        # プレミアムミッション（最初に処理）
        if m.startswith("プレミアムミッション:"):
            m = m.replace("プレミアムミッション:", "<b>Premium Mission:</b> ", 1)
        else:
            # 通常のミッション
            m = m.replace("ミッション:", "<b>Mission:</b> ")
        
        m = m.replace("イベント:", "<b>Event:</b> ")
        m = m.replace("パック開封ポイント:", "<b>Pack Point:</b> ")
        m = m.replace("開封ポイント:", "<b>Pack Point:</b> ")
        m = re.sub(r'(Pack Point:</b>\s*)(\d+)', r'\1\2 points to exchange', m)
        m = m.replace("ポイントで交換", " points to exchange")
        m = m.replace("ポイント", " points")
        
        if "Premium Shop Lineup Update" in m:
            match = re.search(r'Premium Shop Lineup Update\s*(\([^)]+\))?', m)
            if match:
                date_part = match.group(1) if match.group(1) else ""
                m = m.replace(match.group(0), f"Premium Pass Login Bonus{date_part}")
        
        # 先頭の余分なスペースを削除
        m = m.strip()
        methods.append(m)
    
    if not methods: return "No Information"
    return '<ul class="how_to_get">' + "".join(f'<li>{m}</li>' for m in methods) + '</ul>'

def generate_evolution_table(card_data):
    if "進化ステージ" not in card_data: return ""
    chain = [(card_data.get("進化ステージ", "Basic"), [card_data["名前"]])]
    if "進化先" in card_data and card_data["進化先"]:
        for entry in card_data["進化先"].values():
            if isinstance(entry, list) and len(entry) > 0:
                stage_name = entry[0][0] if isinstance(entry[0], list) else "Stage"
                names = [item[1] if isinstance(item, list) else item for item in entry]
                if names: chain.append((stage_name, names))
    if len(chain) <= 1: return ""
    html = '<div class="section"><div class="set-subheading"><h2>Evolution line</h2></div><table class="evolution-line-table">'
    for i, (stage, names) in enumerate(chain):
        html += f'<tr><th>{stage}</th><td>'
        for n in names:
            html += f'<img src="/images/cards/{n}.webp" alt="{n}" class="alternate_art-image">'
        html += '</td></tr>'
        if i < len(chain) - 1:
            html += '<tr><td class="arrow-row" colspan="2"><img src="/images/icon/arrow.webp" class="alternate_art-image"></td></tr>'
    return html + '</table></div>'

def generate_html(data, pack_set_info):
    is_trainer = data.get("カードの種類") == "Trainer"
    card_category = data.get("分類") or ""
    card_name = data["名前"]
    card_series_name = data["収録セット"][0] if data.get("収録セット") else "unknown"
    card_numbers = data.get("カード番号", [])
    first_num = card_numbers[0] if card_numbers else "#"
    if "#" in first_num:
        set_id, num_val = first_num.split("#", 1)
    else:
        set_id, num_val = "unknown", "0"
    
    card_slug = card_name.replace(" ", "_").replace(",", "").replace(".", "").lower()
    set_url = f"/sets/{set_id.lower()}/{card_series_name.lower().replace(' ', '_')}.html"
    card_url = f"/cards/{set_id.lower()}/{num_val}/{card_slug}.html"

    suffix_raw = data.get("特別ルール")
    if isinstance(suffix_raw, list):
        suffix_html = ", ".join(f'<span class="suffix-rule-text">{s}</span>' for s in suffix_raw)
    elif suffix_raw:
        suffix_html = f'<span class="suffix-rule-text">{suffix_raw}</span>'
    else:
        suffix_html = ""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{card_name}</title>
  <link rel="stylesheet" href="/styles/header-footer.css">
  <link rel="stylesheet" href="/styles/card.css">
</head>
<body class="card-page">
  <div id="header"></div>
  <nav class="breadcrumbs">
      <a href="/">Home</a>
      <a href="/cards.html">cards</a>
      <a href="/sets.html">Sets</a>
      <a href="{set_url}">{card_series_name}</a>
      <a href="{card_url}">{card_name}</a>
  </nav>
  <main class="card-page-main">"""

    card_img = f"/images/cards/{first_num.replace('#', '/')}.webp"
    html += f'\n    <img class="card-image" src="{card_img}" alt="{card_name}">\n    <h1>{card_name}</h1>'

    html += f"""
    <div class="section">
      <div class="set-subheading"><h2>Card Information</h2></div>
      <table class="card-info-table">
        <tr><th>Card number</th><td>{generate_card_number_html(data.get("カード番号"))}</td></tr>
        <tr><th>Card type</th><td>{data["カードの種類"]}</td></tr>
        {'<tr><th>Category</th><td>' + card_category + '</td></tr>' if is_trainer else ''}
        <tr><th>Rarity</th><td>{generate_rarity_icons(data.get("レア度"))}</td></tr>
        <tr><th>How to Get</th><td>{generate_how_to_get(data)}</td></tr>
        {generate_sets_info(data, pack_set_info)}
        {generate_packs_info(data, pack_set_info)}
        <tr><th>Suffix rule</th><td>{suffix_html}</td></tr>
        <tr><th>Illustrator</th><td>{data.get("イラストレーター") or ""}</td></tr>
      </table>
    </div>"""

    if is_trainer:
        eff = data.get("カードの効果", {})
        main_effect = eff.get("発動効果", "No effect text.")
        extra_rule = eff.get("追加ルール", "")
        if card_category == "Tool":
            tool_text = "You use Pokémon Tools by attaching them to your Pokémon. You may attach only 1 Pokémon Tool to each Pokémon, and it stays attached."
            extra_rule = tool_text if not extra_rule or extra_rule == "N/A" else f"{extra_rule}<br>{tool_text}"
        has_extra = extra_rule and extra_rule != "N/A"
        html += f"""
    <div class="section">
      <div class="set-subheading"><h2>Effect</h2></div>
      <div class="trainer-effect-box">
        <p class="description-text">{main_effect}</p>
        {'<hr class="set-border">' if has_extra else ''}
        {f'<p class="rules-text"><i>{extra_rule}</i></p>' if has_extra else ''}
      </div>
    </div>"""
    else:
        retreat_cost = data.get("にげる", 0)
        retreat_icons = "".join(f'<img src="{energy_icon_map["colorless"]}" class="energy-icon">' for _ in range(int(retreat_cost))) if str(retreat_cost).isdigit() else "None"
        html += f"""
    <div class="section">
      <div class="set-subheading"><h2>Stats</h2></div>
      <table class="card-info-table">
        <tr><th>Stage</th><td>{data.get("進化ステージ", "Basic")}</td></tr>
        <tr><th>HP</th><td>{data.get("HP", "0")}</td></tr>
        <tr><th>Type</th><td><img src="{energy_icon_map.get(data.get('タイプ', '').lower(), '')}" class="energy-icon"> {data.get("タイプ", "")}</td></tr>
        <tr><th>Weakness</th><td>{generate_weakness_html(data.get("弱点"))}</td></tr>
        <tr><th>Retreat</th><td>{retreat_icons}</td></tr>
      </table>
    </div>
    <div class="section">
      <div class="set-subheading"><h2>Description</h2></div>
      <p class="description-text">{data.get("説明文", "")}</p>
    </div>"""
        attacks = data.get("ワザ", [])
        if attacks:
            html += '<div class="section"><div class="set-subheading"><h2>Ability・Attacks</h2></div><ul class="attack">'
            for i, attack in enumerate(attacks):
                cost = "".join(f'<img src="{energy_icon_map.get(t.lower(), "")}" class="energy-icon">' for t in attack.get("エネルギータイプ", []))
                html += f'<li><div class="attack-table"><div class="attack-cell cost">{cost}</div><div class="attack-cell name">{attack.get("名前", "")}</div><div class="attack-cell damage">{attack.get("ダメージ", "0")}</div></div>'
                effect_raw = attack.get("効果", "N/A")
                html += f'<div class="attack-effect">{effect_raw if effect_raw != "N/A" else "&nbsp;"}</div>'
                if i < len(attacks) - 1: html += '<hr class="attack-divider">'
                html += '</li>'
            html += '</ul></div>'

    alt_arts = data.get("Alternate Arts", [])
    if alt_arts:
        html += '<div class="section"><div class="set-subheading"><h2>Alternate Art</h2></div><div class="sets-wrapper"><div class="sets-inner-scroll"><ul class="alternate_art">'
        for art in alt_arts:
            c_num = art.get("カード番号", "")
            if "#" in c_num:
                img_path = f"/images/cards/{c_num.replace('#', '/')}.webp"
                link_url = f"/cards/{c_num.replace('#', '/')}/{card_slug}.html"
                set_code, num = c_num.split("#", 1)
                html += f'''<li class="set-item">
                    <a href="{link_url}">
                        <img src="{img_path}" alt="Alternate Art {c_num}" class="alternate_art-image">
                    </a>
                        <div class="card-number-alternate_art">
                            <span class="card-set-code">{set_code}</span><span>{num}</span>
                        </div>
                </li>'''
        html += '</ul></div></div></div>'

    flair_key = "エフェクト効果" if is_trainer else "エフェクト一覧"
    flairs = data.get(flair_key, [])
    html += '<div class="section"><div class="set-subheading"><h2>Flairs</h2></div>'
    if isinstance(flairs, list) and len(flairs) > 0:
        html += '<ul class="flairs">' + "".join(f'<li><img src="/images/card_effect/{f}" class="flairs-image"></li>' for f in flairs) + '</ul>'
    else:
        html += '<p>None</p>'
    html += '</div>'
    if not is_trainer: html += generate_evolution_table(data)
    html += '</main><div id="footer"></div><script src="/js/header-footer-load.js"></script></body></html>'
    return html

# --- 実際の変換処理 (別スレッドで実行) ---
def run_conversion(target_dir, progress_bar, label_var, percent_var, progress_win):
    pack_set_info = load_pack_set_info()
    all_json_files = []
    for root_path, dirs, files in os.walk(target_dir):
        for filename in files:
            if filename.lower().endswith(".json") and filename != "pack_set_name.json":
                all_json_files.append(os.path.join(root_path, filename))

    total_files = len(all_json_files)
    if total_files == 0:
        messagebox.showwarning("なし", "JSONが見つかりませんでした。")
        progress_win.destroy()
        return

    progress_bar["maximum"] = total_files
    processed_count = 0

    for json_path in all_json_files:
        try:
            current_file = os.path.basename(json_path)
            label_var.set(f"処理中: {current_file}")
            progress_bar['value'] = processed_count
            percent_var.set(f"{int((processed_count / total_files) * 100)}% ({processed_count}/{total_files})")
            
            with open(json_path, "r", encoding="utf-8") as f:
                card_data = json.load(f)
            
            html_content = generate_html(card_data, pack_set_info)
            
            # ===== 出力先を pyフォルダと同階層の cards フォルダに変更 =====
            card_name = os.path.splitext(os.path.basename(json_path))[0]
            path_parts = json_path.split(os.sep)
            
            if "cards_json" in path_parts:
                cards_index = path_parts.index("cards_json")
                set_code = path_parts[cards_index + 1]
                card_num = path_parts[cards_index + 2]
                
                output_dir = os.path.join("..", "..", "cards", set_code, card_num)
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{card_name}.html")
            else:
                output_path = os.path.splitext(json_path)[0] + ".html"
            # ============================================================
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            processed_count += 1
        except Exception as e:
            print(f"Error: {e}")

    progress_win.destroy()
    messagebox.showinfo("完了", f"合計 {processed_count} 件のHTMLを生成しました。")

# --- メインウィンドウと起動 ---
def start_app():
    root = tk.Tk()
    root.title("HTML Generator")
    # メインウィンドウを最初から小さく表示（完全に消すと不具合が出るため）
    root.geometry("300x100")

    def on_click():
        target_dir = filedialog.askdirectory(title="cardsフォルダを選択してください")
        if not target_dir:
            return

        # 進捗ウィンドウ（メインウィンドウの上に作成）
        progress_win = tk.Toplevel(root)
        progress_win.title("Generating...")
        progress_win.geometry("450x150")
        
        label_var = tk.StringVar(value="準備中...")
        tk.Label(progress_win, textvariable=label_var, wraplength=400).pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_win, length=350, mode='determinate')
        progress_bar.pack(pady=5)
        
        percent_var = tk.StringVar(value="0%")
        tk.Label(progress_win, textvariable=percent_var).pack()

        # 別スレッドで重い処理を開始
        thread = threading.Thread(target=run_conversion, args=(target_dir, progress_bar, label_var, percent_var, progress_win))
        thread.start()

    tk.Button(root, text="cardsフォルダを選択して実行", command=on_click, height=2, width=25).pack(expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    start_app()
