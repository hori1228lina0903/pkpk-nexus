import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import os
import random
from io import BytesIO
from PIL import Image, ImageOps
import numpy as np
import json
import cloudscraper
import time

# -------- 基本情報の取得 -------- #
def get_urls_from_json(json_path):
    # JSONファイルを読み込み
    with open(json_path, "r", encoding="utf-8") as f:
        urls = json.load(f)  # 直接リストとして読み込まれる
    return urls
    
def get_card_image(soup):
    try:
        # カード番号を取得
        card_numbers = get_card_number(soup)
        
        # 画像タグを取得（複数対応）
        img_tags = soup.select("div.game-card-image__inner img")
        if not img_tags:
            print("❌ 画像タグが見つかりません")
            return "N/A"

        image_urls = []
        
        # 各カード番号と画像を処理
        for i, card_number in enumerate(card_numbers):
            # 対応する画像を取得（インデックスが範囲内かチェック）
            if i < len(img_tags):
                tag = img_tags[i]
                image_url = tag.get("src")
                if not image_url:
                    print(f"❌ 画像URLが取得できません: {tag}")
                    continue
                    
                image_urls.append(image_url)
                
                # card_number からフォルダ名とファイル名を分割
                try:
                    folder_part, file_part = card_number.split("#")
                except ValueError:
                    print(f"❌ card_number の形式が不正です: {card_number}")
                    continue

                # 保存先パスの生成
                folder_path = os.path.join("images", "cards", folder_part)
                folder_path = os.path.join("..", "..", "images", "cards", folder_part)
                os.makedirs(folder_path, exist_ok=True)

                file_path = os.path.join(folder_path, f"{file_part}.webp")

                # すでに画像ファイルが存在する場合はスキップ
                if os.path.exists(file_path):
                    print(f"⏩ 画像は既に存在しています: {file_path}")
                    continue

                # ダウンロード → 加工 → 保存
                try:
                    # 画像ダウンロード前に待機
                    time.sleep(random.uniform(1, 3))
                    
                    # cloudscraperを使用して画像をダウンロード
                    if use_cloudscraper:
                        response = scraper.get(image_url, timeout=30)
                    else:
                        response = requests.get(image_url, timeout=30)
                    
                    response.raise_for_status()
                    
                    # レスポンスが画像かどうかをチェック
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' not in content_type:
                        print(f"⚠️ 画像でないコンテンツを受信しました: {content_type}")
                        # デバッグ用にファイルを保存
                        with open(f"debug_{file_part}.html", "wb") as f:
                            f.write(response.content)
                        continue

                    img = Image.open(BytesIO(response.content)).convert("RGB")
                    img = add_noise_and_crop(img)

                    img.save(file_path, format="WEBP", quality=95)
                    print(f"✅ 画像保存（加工済み）完了: {file_path}")
                except Exception as e:
                    print(f"❌ 画像のダウンロードまたは加工に失敗: {e}")
                    # エラー内容を詳細に表示
                    import traceback
                    traceback.print_exc()
        
        # 最初の画像URLを返す（後方互換性のため）
        return image_urls[0] if image_urls else "N/A"
        
    except Exception as e:
        print(f"Error in get_card_image: {e}")
        import traceback
        traceback.print_exc()
        return "N/A"
    
def rarity_icons(soup):
    try:
        # レアリティタイプと出現回数を記録する辞書
        rarity_count = {}
        
        # rarityアイコンをすべて取得（span要素を検索）
        icons = soup.select("span.rarity-icon__icon")

        for icon in icons:
            # card-variant-gallery内のアイコンは除外（Alternate Prints）
            if icon.find_parent(class_="card-variant-gallery"):
                continue
                
            class_names = icon.get('class', [])
            for cls in class_names:
                if cls.startswith('rarity-icon__icon--'):
                    rarity_type = cls.replace('rarity-icon__icon--', '')
                    # 出現回数をカウント
                    rarity_count[rarity_type] = rarity_count.get(rarity_type, 0) + 1
                    break  # 1つのアイコンに1つのレアリティタイプのみ

        # 結果をリスト形式に変換
        rarity_types = list(rarity_count.keys())
        total_count = sum(rarity_count.values())

        return {
            'rarity_types': rarity_types,
            'count': total_count
        }

    except Exception as e:
        print(f"Error extracting rarity icons: {e}")
        return {'rarity_types': [], 'count': 0}

def get_card_name(soup):
    tag = soup.select_one("h1.fs-1.text-break")
    if tag:
        name = tag.text.strip()
        return name
    return "N/A"
    
def get_card_number(soup):
    try:
        card_numbers = []
        
        # メインカードのセット情報を取得
        set_summaries = soup.select("div.card-collection-summary")
        
        # Alternate Printsセクションを除外
        main_summaries = []
        for summary in set_summaries:
            if summary.find_parent("div", class_="card-variant-gallery"):
                continue
            main_summaries.append(summary)
        
        for summary in main_summaries:
            set_code_tag = summary.select_one("div.card-collection-summary__name a")
            if not set_code_tag:
                continue
                
            href = set_code_tag.get("href", "")
            set_code = href.split("/")[2] if href and len(href.split("/")) > 2 else "N/A"
            
            card_num_tag = summary.select_one("div.card-collection-summary__meta span:first-child")
            if not card_num_tag:
                continue
                
            card_num_text = card_num_tag.text.strip()
            card_num = ''.join(filter(str.isdigit, card_num_text))
            
            if card_num and set_code != "N/A":
                card_numbers.append(f"{set_code}#{card_num}")
        
        card_numbers.sort(key=natural_sort_key)
        
        if not card_numbers:
            return ["N/A"]
            
        return card_numbers
        
    except Exception as e:
        print(f"Error extracting card number: {e}")
        return ["N/A"]
           
def get_hp(soup):
    # 方法1: ポケモンカード用のHP表示（既存の方法）
    tag = soup.select_one("div.fw-bold span.fs-1.lh-1")
    if tag:
        hp_text = tag.text.strip()
        # 数字だけを抽出（例: "120"）
        numbers = ''.join(filter(str.isdigit, hp_text))
        return numbers if numbers else "N/A"
    
    # 方法2: トレーナーカード（特にFossilカード）のHPを取得
    # カードの説明文からHP情報を探す
    desc_div = soup.select_one("div.card-detail__desc")
    if desc_div:
        desc_text = desc_div.get_text()
        # HPパターンを検索（例: "40-HP", "50-HP", "60-HP" など）
        hp_pattern = r'(\d+)-HP'
        match = re.search(hp_pattern, desc_text, re.IGNORECASE)
        if match:
            # 数字だけを返す（例: "40"）
            return match.group(1)
    
    return "N/A"


def get_type(soup):
    tag = soup.select_one("span.energy-icon")
    if tag:
        for cls in tag["class"]:
            if cls.startswith("energy-icon--type-"):
                return cls.replace("energy-icon--type-", "")
    return "N/A"


def get_weakness(soup):
    container = soup.find("div", class_="d-inline-flex", string=None)
    if container:
        type_icon = container.select_one(".energy-icon")
        multiplier_divs = container.select("div")
        multiplier = multiplier_divs[-1].text.strip() if multiplier_divs else ""
        if type_icon:
            for cls in type_icon["class"]:
                if cls.startswith("energy-icon--type-"):
                    return f"{cls.replace('energy-icon--type-', '')} {multiplier}"
    return "N/A"


def get_retreat_cost(soup):
    label = soup.find("div", class_="mb-1", string="Retreat")
    if label:
        parent = label.find_parent("div", class_="flex-1")
        if parent:
            return len(parent.select(".energy-icon"))
    return 0

# -------- 説明文を取得 -------- #
def get_card_description(soup):
    description_data = {}
    
    # ポケモンカードの説明文を検索（斜体のテキスト）
    italic_text = soup.select_one("div.fst-italic")
    if italic_text:
        # テキストを取得して改行をスペースに置換
        raw_text = italic_text.get_text()
        # 改行をスペースに、連続する空白を単一スペースに
        cleaned_text = re.sub(r'\s+', ' ', raw_text.replace('\n', ' ')).strip()
        description_data["説明文"] = cleaned_text
    
    # トレーナーカードの説明文を検索
    trainer_desc = soup.select_one("div.card-detail__desc")
    if trainer_desc:
        # テキストを取得して改行をスペースに置換
        raw_text = trainer_desc.get_text()
        # 改行をスペースに、連続する空白を単一スペースに
        cleaned_text = re.sub(r'\s+', ' ', raw_text.replace('\n', ' ')).strip()
        description_data["説明文"] = cleaned_text
    
    return description_data
    
# -------- イラストレーター -------- #
def get_illustrator(soup):
    for div in soup.select("div.d-grid.gap-2.small.lh-sm div"):
        text = div.get_text(strip=True)
        if "Illustrated by" in text:
            return text.replace("Illustrated by", "").strip()
    return "N/A"
    
def get_card_series_and_packs(soup, rarity_counts):
    """カードの入手方法を取得（セット情報も別途返す）"""
    try:
        card_sources = []
        set_values = []  # セット情報を格納
        has_pack_source = False
        
        # イベント判定用のヘルパー関数
        def is_event_text(text):
            """テキストがイベント関連かどうかを判定（大文字小文字区別なし）"""
            text_lower = text.lower()
            return "event" in text_lower or "wonder pick" in text_lower
        
        # カードの入手方法
        # 構造1: パックでの入手方法
        pack_items = soup.select("div.card-detail__pack")
        for item in pack_items:
            pack_name_tag = item.select_one("div.card-detail__pack__name a")
            if pack_name_tag:
                pack_text = pack_name_tag.text.strip()
                # テキストを変換
                processed_text = process_premium_mission_text(pack_text)
                
                # イベント判定（大文字小文字区別なし）
                if is_event_text(processed_text):
                    card_sources.append(f"イベント: {processed_text}")
                else:
                    card_sources.append(f"パック: {processed_text}")
                
                has_pack_source = True
        
        # 構造2: ピックでの入手方法（イベント）
        pick_items = soup.select("div.card-detail__pick")
        for item in pick_items:
            pick_name_tag = item.select_one("div.card-detail__pick__name a")
            if pick_name_tag:
                pick_text = pick_name_tag.text.strip()
                processed_text = process_premium_mission_text(pick_text)
                
                # イベント判定（大文字小文字区別なし）
                if is_event_text(processed_text):
                    card_sources.append(f"イベント: {processed_text}")
                else:
                    card_sources.append(f"ピック: {processed_text}")
        
        # 構造3: ミッションでの入手方法
        mission_items = soup.select("div.card-detail__mission")
        for item in mission_items:
            mission_name_tag = item.select_one("div.card-detail__mission__name a")
            if mission_name_tag:
                mission_text = mission_name_tag.text.strip()
                processed_text = process_premium_mission_text(mission_text)
                
                # プレミアムミッションか通常ミッションか、イベントかを判定
                if "Premium" in mission_text or "premium" in mission_text:
                    card_sources.append(f"プレミアムミッション: {processed_text}")
                elif is_event_text(processed_text):
                    card_sources.append(f"イベント: {processed_text}")
                else:
                    card_sources.append(f"ミッション: {processed_text}")
        
        # 構造4: ガイド記事形式
        guide_items = soup.select("div.card-detail__sourced_guide")
        for item in guide_items:
            guide_name_tag = item.select_one("div.card-detail__sourced_guide__name a")
            if guide_name_tag:
                guide_text = guide_name_tag.text.strip()
                processed_text = process_premium_mission_text(guide_text)
                
                # Premium Shop関連はプレミアムミッションとして扱う
                if "Premium Shop" in guide_text:
                    card_sources.append(f"プレミアムミッション: {processed_text}")
                elif is_event_text(processed_text):
                    card_sources.append(f"イベント: {processed_text}")
                else:
                    card_sources.append(f"ガイド: {processed_text}")
        
        # 構造5: ショップ商品形式
        shop_items = soup.select("div.card-detail__shop_product")
        for item in shop_items:
            shop_name_tag = item.select_one("div.card-detail__shop_product__name a")
            if shop_name_tag:
                shop_text = shop_name_tag.text.strip()
                processed_text = process_premium_mission_text(shop_text)
                
                # Premium Shop関連はプレミアムミッションとして扱う
                if "Premium Shop" in shop_text:
                    card_sources.append(f"プレミアムミッション: {processed_text}")
                elif is_event_text(processed_text):
                    card_sources.append(f"イベント: {processed_text}")
                else:
                    card_sources.append(f"商品: {processed_text}")
        
        # パック開封ポイントの計算
        if has_pack_source and rarity_counts:
            points = calculate_pack_points(rarity_counts)
            if points > 0:
                card_sources.append(f"パック開封ポイント: {points}")
                print(f"📦 パック開封ポイント: {points} (レア度: {rarity_counts.get('rarity_types', [])})")
        elif not has_pack_source:
            print(f"ℹ️ パックからの入手方法がないためパック開封ポイントを追加しません")
        
        # セット情報の取得（Setsセクションから）
        set_summaries = soup.select("div.card-collection-summary")
        for summary in set_summaries:
            set_name_tag = summary.select_one("div.card-collection-summary__name a")
            if set_name_tag:
                set_name = set_name_tag.text.strip()
                set_values.append(set_name)
        
        # 重複を排除
        set_values = list(dict.fromkeys(set_values))
        
        if not card_sources:
            card_sources = ["情報なし"]
        
        # タプルで返す：(カード入手方法リスト, セット値リスト)
        return card_sources, set_values
        
    except Exception as e:
        print(f"Error extracting card series and packs: {e}")
        return ["情報なし"], []

def process_premium_mission_text(text):
    """
    プレミアムミッション関連のテキストを統一フォーマットに変換
    """
    try:
        # パターン1: Log in (Day X) - YYYY Month Premium Shop
        pattern1 = r'Log in \(Day (\d+)\) - (\w+ \d{4}) Premium Shop'
        match = re.search(pattern1, text, re.IGNORECASE)
        
        if match:
            day_num = match.group(1)
            month_year = match.group(2)
            converted = f"{month_year} Login Bonus (Day {day_num})"
            print(f"  🔄 パターン1変換: '{text}' -> '{converted}'")
            return converted
        
        # パターン2: Premium Shop Lineup Update/Updated (Month YYYY)
        # 例: Premium Shop Lineup Updated (January 2025)
        pattern2 = r'Premium Shop Lineup Updated? \((\w+ \d{4})\)'
        match = re.search(pattern2, text, re.IGNORECASE)
        
        if match:
            month_year = match.group(1)
            # Day情報がない場合は (Day 1) をデフォルトで付ける
            converted = f"{month_year} Login Bonus (Day 1)"
            print(f"  🔄 パターン2変換: '{text}' -> '{converted}'")
            return converted
        
        # その他のPremium Shop関連テキスト
        if "Premium Shop" in text:
            # 年月を抽出できるか試す
            year_pattern = r'\((\w+ \d{4})\)'
            match = re.search(year_pattern, text)
            if match:
                month_year = match.group(1)
                converted = f"{month_year} Login Bonus (Day 1)"
                print(f"  🔄 Premium Shop変換: '{text}' -> '{converted}'")
                return converted
        
        return text
        
    except Exception as e:
        print(f"⚠️ テキスト変換中にエラー: {e}")
        return text

def calculate_pack_points(retreat_cost):
    """レア度に基づいてパック開封ポイントを計算"""
    try:
        rarity_types = retreat_cost.get("rarity_types", [])
        count = retreat_cost.get("count", 0)
        
        if not rarity_types or count == 0:
            return 0
        
        rarity_type = rarity_types[0]  # 最初のレア度タイプを使用
        
        # レア度に応じたポイント計算
        if rarity_type == "diamond":
            if count == 1:
                return 35
            elif count == 2:
                return 70
            elif count == 3:
                return 150
            elif count == 4:
                return 500
        elif rarity_type == "star":
            if count == 1:
                return 400
            elif count == 2:
                return 1250
            elif count == 3:
                return 1500
        elif rarity_type == "shiny":
            if count == 1:
                return 1000
            elif count == 2:
                return 1350
        elif rarity_type == "crown":
            return 2500
        
        return 0
        
    except Exception as e:
        print(f"Error calculating pack points: {e}")
        return 0

def get_abilities(soup):
    abilities = []

    # 複数の特性に対応（リストで返す）
    ability_rows = soup.select("div.ability-summary-row")
    for row in ability_rows:
        name_div = row.select_one("div.ability-summary-row__name")
        desc_div = row.select_one("div.ability-summary-row__description")

        if name_div and desc_div:
            # "Ability Safeguard" のうち "Safeguard" だけ取り出す
            name = name_div.get_text(strip=True).replace("Ability", "").strip()
            # 効果テキストはstrongなど含めてテキストだけ抽出
            description = desc_div.get_text(strip=True)
            abilities.append({"name": name, "effect": description})

    return abilities


def get_attacks(soup):
    attacks = []
    for row in soup.select(".attack-summary-row"):
        atk_name = row.select_one(".attack-summary-row__name")
        damage = row.select_one(".attack-summary-row__damage")
        effect = row.select_one(".attack-summary-row__footer")
        cost_icons = row.select(".attack-summary-row__costs .energy-icon")

        energy_types = [
            cls.replace("energy-icon--type-", "")
            for icon in cost_icons
            for cls in icon["class"]
            if cls.startswith("energy-icon--type-")
        ]

        attacks.append(
            {
                "name": atk_name.text.strip() if atk_name else "N/A",
                "damage": damage.text.strip() if damage else "N/A",
                "effect": effect.text.strip() if effect else "N/A",
                "energy_cost": len(energy_types),
                "energy_types": energy_types,
            }
        )
    return attacks

def get_alternate_arts(soup):
    arts = []
    for item in soup.select("div.card-variant-gallery__list-item"):
        link = item.select_one("a")
        href = link["href"] if link and "href" in link.attrs else ""
        parts = href.strip("/").split("/")
        alt_card_number = f"{parts[1]}#{parts[2]}" if len(parts) >= 3 else None
        if alt_card_number:
            arts.append(alt_card_number)
    
    # メインカード番号を取得
    main_card_numbers = get_card_number(soup)
    
    # メインカード番号と重複するものを除外
    unique_arts = []
    for art in arts:
        if art not in main_card_numbers:
            unique_arts.append(art)
    
    unique_arts.sort(key=natural_sort_key)
    return unique_arts
    
def natural_sort_key(card_num):
    parts = []
    current_part = ""
    last_char_type = None
    
    for char in card_num:
        if char.isalpha():
            current_char_type = 'alpha'
        elif char.isdigit():
            current_char_type = 'digit'
        else:
            current_char_type = 'other'
        
        if last_char_type != current_char_type and current_part:
            parts.append(current_part)
            current_part = ""
        
        current_part += char
        last_char_type = current_char_type
    
    if current_part:
        parts.append(current_part)
    
    sort_key = []
    for part in parts:
        if part.isdigit():
            sort_key.append(int(part))
        else:
            sort_key.append(part)
    
    return sort_key

# -------- カード種類と進化ステージ -------- #
def get_card_type_and_stage(soup, name, hp):
    header = soup.select_one("div.heading-container")
    if header:
        tag = header.select_one("div.fw-bold")
        if tag:
            parts = [p.strip() for p in tag.get_text(separator="|", strip=True).split("|")]
            if len(parts) >= 2:
                card_type = parts[0]
                stage = parts[1]
                extra = parts[2:] if len(parts) > 2 else []
                
                unique_card_types = []
                if "Ultra Beast" in extra:
                    unique_card_types.append("Ultra Beast")
                
                # 名前を小文字にして判定
                name_lower = name.lower()

                # 先頭が "mega " (mega + スペース) の場合のみ Mega と判定
                if name_lower.startswith("mega "):
                    unique_card_types.append("Mega")
                
                # 名前のどこかに " ex" (スペース + ex) があれば追加
                # Mega Pinsir ex のようなケースで両方追加されるように elif ではなく if を使用
                elif " ex" in name_lower:
                    unique_card_types.append("ex")
                # --- ここまで修正部分 ---
                
                # ワザを取得してチェック
                attacks = get_attacks(soup)
                if attacks:
                    # 全てのワザのエネルギータイプをチェック
                    all_unspecified = True
                    for attack in attacks:
                        energy_types = attack.get("energy_types", [])
                        # "unspecified"が含まれていないかチェック
                        has_specified_energy = False
                        for energy_type in energy_types:
                            if energy_type != "unspecified" and energy_type:
                                has_specified_energy = True
                                break
                        
                        if has_specified_energy:
                            all_unspecified = False
                            break
                    
                    # 全てのワザがunspecifiedまたは空の場合
                    if all_unspecified:
                        unique_card_types.append("Baby")
                
                if not unique_card_types:
                    unique_card_types = None

                return card_type, stage, unique_card_types
    return "N/A", "N/A", None
    
# -------- トレーナーカード効果取得 -------- #
def get_card_effect(soup):
    # --- card-detail__desc を取得 ---
    desc_text_parts = []
    desc_div = soup.select_one("div.card-detail__desc")
    if desc_div:
        for element in desc_div.contents:
            if element.name == "span":
                # エネルギー記号
                classes = element.get("class", [])
                for cls in classes:
                    if cls.startswith("energy-text--type-"):
                        energy_type = cls.replace("energy-text--type-", "")
                        desc_text_parts.append(f"[{energy_type.capitalize()}]")
            elif element.string:
                desc_text_parts.append(element.string)

    # 改行・余分なスペースを整形
    card_effect = " ".join("".join(desc_text_parts).split()) if desc_text_parts else "N/A"

    # --- card-detail__rules を取得 ---
    rules_div = soup.select_one("div.card-detail__rules")
    additional_rules = rules_div.get_text(" ", strip=True) if rules_div else "N/A"

    return {
        "発動効果": card_effect,
        "追加ルール": additional_rules
    }

# -------- Evolves into -------- #
# ランダムUser-Agentの候補リスト
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
]

# ベースURL（必要に応じて定義）
base_url = "https://www.pokemon-zone.com"

def fetch_with_random_ua(url):
    """ランダムなUser-Agentでページを取得"""
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # ステータスコードが異常な場合例外を発生
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
        
# -------- Evolves into -------- #
def fetch_ev_into(soup, ev_into_dict):
    # カードの種類と進化段階を取得
    card_type, card_stage, is_ultra_beast = get_card_type_and_stage(soup, name, hp)
    
    # 進化ラベルを決定
    stage_clean = card_stage.strip()
    if stage_clean == "Basic":
        label = "Stage 1"
    elif stage_clean == "Stage 1":
        label = "Stage 2"
    else:
        label = "Stage 1"
    
    print(f"現在のステージ: {stage_clean} -> 進化ラベル: {label}")
    
    # "Evolves into:"を含むdivを検索
    for div in soup.select("div"):
        text_content = div.text.strip()
        if "Evolves into:" in text_content:
            # "Evolves into:"の後のテキストを抽出
            evolves_into_text = text_content.split("Evolves into:")[-1].strip()
            
            # 最初の行を取得（リンクテキストだけ）
            evolves_into_pokemon = evolves_into_text.split('\n')[0].strip()
            
            if evolves_into_pokemon:
                # 辞書に保存（depth=0で固定）
                ev_into_dict.setdefault(0, [])
                if (label, evolves_into_pokemon) not in ev_into_dict[0]:
                    ev_into_dict[0].append((label, evolves_into_pokemon))
                    print(f"進化先を追加: {label} - {evolves_into_pokemon}")
            break
    
    return ev_into_dict
            
# -------- Evolves from -------- #
def fetch_ev_from(soup, ev_from_dict):
    card_type, card_stage, is_ultra_beast = get_card_type_and_stage(soup, name, hp)
    stage_clean = card_stage.strip()
    if stage_clean == "Stage 1":
        label = "Basic"
    elif stage_clean == "Stage 2":
        label = "Stage 1"
    else:
        label = "進化"
        
    print(f"現在のステージ: {stage_clean} -> 進化元ラベル: {label}")
    
    # 方法1: カードヘッダー部分から進化元を取得
    header_div = soup.select_one("div.fw-bold")
    if header_div and "Evolves from" in header_div.get_text():
        # ヘッダー内のリンクから進化元を取得
        for a in header_div.select("a[href^='/pokemon/']"):
            evolves_from_pokemon = a.text.strip()
            if evolves_from_pokemon:
                ev_from_dict.setdefault(0, [])
                if (label, evolves_from_pokemon) not in ev_from_dict[0]:
                    ev_from_dict[0].append((label, evolves_from_pokemon))
                    print(f"進化元を追加: {label} - {evolves_from_pokemon}")
                break
    
    # 方法2: もしヘッダーで見つからなかった場合、下部の進化情報から取得
    if not ev_from_dict.get(0):
        for div in soup.select("div"):
            text_content = div.text.strip()
            if "evolves from" in text_content.lower():
                # リンクがある場合はリンクテキストを優先
                links = div.select("a[href^='/pokemon/']")
                if links:
                    for a in links:
                        evolves_from_pokemon = a.text.strip()
                        if evolves_from_pokemon:
                            ev_from_dict.setdefault(0, [])
                            if (label, evolves_from_pokemon) not in ev_from_dict[0]:
                                ev_from_dict[0].append((label, evolves_from_pokemon))
                                print(f"進化元を追加: {label} - {evolves_from_pokemon}")
                            break
                else:
                    # リンクがない場合はテキストから抽出
                    evolves_from_text = text_content.split("evolves from")[-1].strip()
                    evolves_from_pokemon = evolves_from_text.split('\n')[0].strip()
                    evolves_from_pokemon = evolves_from_pokemon.lstrip(':').strip()
                    
                    if evolves_from_pokemon:
                        ev_from_dict.setdefault(0, [])
                        if (label, evolves_from_pokemon) not in ev_from_dict[0]:
                            ev_from_dict[0].append((label, evolves_from_pokemon))
                            print(f"進化元を追加: {label} - {evolves_from_pokemon}")
                break
    
    return ev_from_dict
                
# -------- 画像加工 -------- #
def add_noise_and_crop(img):
    
    np_img = np.array(img).astype(np.int16)

    noise = np.random.normal(0, 5, np_img.shape)
    
    noisy_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(noisy_img)
    
    width, height = img.size
    crop_area = (2, 2, width - 2, height - 2)
    img = img.crop(crop_area)

    return img

# -------- カードエフェクトを取得 -------- #
def get_flair_titles(soup):
    # デバッグ: 受け取ったHTMLをファイルに保存
    debug_file_path = "debug_flair_page.html"
    with open(debug_file_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"📄 デバッグHTMLを保存しました: {debug_file_path}")
    
    # ページのtitleタグを確認（Cloudflareチャレンジかどうか）
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.text.strip()
        print(f"📌 ページタイトル: {title_text}")
        if "Just a moment" in title_text or "Cloudflare" in title_text:
            print("⚠️ Cloudflareチャレンジページの可能性があります")
            return []
    
    flair_titles = []  # 順序を保持するリスト
    seen_titles = set()  # 重複チェック用のセット
    flair_data = []

    print("🔍 Flair要素の検索を開始...")
    
    # 方法1: 現在の方法（title属性から検索）
    flair_elements = []
    for tag in soup.find_all(attrs={"title": True}):
        title = tag["title"]
        if "Flair" in title:
            flair_elements.append(tag)
            print(f"  ✅ title属性でFlairを発見: {title}")
    
    if not flair_elements:
        print("❌ title属性でFlair要素が見つかりませんでした")
        # 方法2: 画像タグを直接検索
        print("🔍 imgタグを直接検索...")
        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src", "")
            alt = img.get("alt", "")
            if "flair" in src.lower() or "flair" in alt.lower():
                print(f"  ✅ imgタグでFlairを発見: src={src}, alt={alt}")
                flair_elements.append(img)
    
    if not flair_elements:
        print("❌ どの方法でもFlair要素が見つかりませんでした")
        # デバッグ用に全ての画像タグを表示
        print("📋 ページ内の全てのimgタグ:")
        all_imgs = soup.find_all("img")
        for i, img in enumerate(all_imgs[:10]):  # 最初の10個だけ表示
            src = img.get("src", "")
            alt = img.get("alt", "")
            classes = img.get("class", [])
            print(f"  {i+1}. src={src[:50]}..., alt={alt}, class={classes}")
        return []

    print(f"🎯 合計{len(flair_elements)}個のFlair要素を発見")

    for tag in flair_elements:
        title = tag.get("title", "")
        if not title and "Flair" not in title:
            # titleがない場合、altや他の属性を確認
            alt = tag.get("alt", "")
            if "Flair" in alt:
                title = alt
            else:
                continue
        
        preview = tag.find("span", class_="common-item-preview")
        image_url = None
        
        # URLを取得する方法を複数試す
        if preview and "style" in preview.attrs:
            match = re.search(r'url\((.*?)\)', preview["style"])
            if match:
                image_url = match.group(1)
                print(f"  📍 style属性からURL取得: {image_url[:50]}...")
        
        # style属性がない場合は、imgタグのsrcを確認
        if not image_url and tag.name == "img":
            image_url = tag.get("src", "")
            if image_url:
                print(f"  📍 imgタグのsrcからURL取得: {image_url[:50]}...")
        
        # data-srcなどの属性も確認
        if not image_url:
            for attr in ["data-src", "data-url", "data-image"]:
                if attr in tag.attrs:
                    image_url = tag[attr]
                    print(f"  📍 {attr}属性からURL取得: {image_url[:50]}...")
                    break
        
        if image_url:
            # 画像保存用に使うファイル名形式に変換
            # 改行文字を削除してから処理
            title_clean = title.replace('\n', ' ').replace('\r', ' ')
            filename = re.sub(r"[():]", "", title_clean).replace(" ", "_").replace("/", "_") + ".webp"
            
            # 特殊文字をさらに処理（改行、タブなど）
            filename = re.sub(r'[\n\r\t]', '', filename)
            filename = re.sub(r'[<>\"\'|?*]', '', filename)
            
            # ファイル名が空でないことを確認
            if not filename or filename.isspace():
                print(f"⚠️ 無効なファイル名: '{title}' -> スキップします")
                continue
                
            flair_data.append((title, image_url, filename))
            
            # 重複を排除して追加
            if filename not in seen_titles:
                seen_titles.add(filename)
                # Starting Flairを特定して先頭に追加
                if "Sparkles Flair: Gold (Cosmetic)" in title:
                    flair_titles.insert(0, filename)  # 先頭に追加
                    print(f"  👑 Starting Flairを先頭に追加: {filename}")
                else:
                    flair_titles.append(filename)
                    print(f"  ➕ Flairを追加: {filename}")

    if not flair_data:
        print("❌ Flairデータが見つかりませんでした")
        # ページ内の構造をさらに詳細に分析
        print("🔍 ページ構造の詳細分析...")
        
        # Flairセクションを探す
        flair_sections = soup.find_all(string=re.compile("Flair", re.IGNORECASE))
        for section in flair_sections[:5]:
            print(f"  📍 'Flair'を含むテキスト: {section[:100]}...")
            
        # すべての画像をチェック
        all_images = soup.find_all("img")
        print(f"  📊 ページ内のimgタグ総数: {len(all_images)}")
        
        return []
        
    output_folder = os.path.join("..", "..", "images", "card_effect")
    os.makedirs(output_folder, exist_ok=True)

    print(f"🔄 {len(flair_data)}個のFlair画像を処理します...")

    processed_count = 0
    for title, url, filename in flair_data:
        # 重複排除：同じファイル名は1回だけ処理
        if filename not in seen_titles:
            continue
            
        filepath = os.path.join(output_folder, filename)
        
        if os.path.exists(filepath):
            print(f"⏩ 既存のためスキップ: {filename}")
            seen_titles.discard(filename)  # 処理済みなので除外
            processed_count += 1
            continue

        try:
            # ダウンロード前に待機
            wait_time = random.uniform(1, 3)
            print(f"⏳ {wait_time:.1f}秒待機してから {filename} をダウンロード...")
            time.sleep(wait_time)
            
            # URLが相対パスの場合は絶対URLに変換
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = "https://www.pokemon-zone.com" + url
            
            print(f"🌐 ダウンロードURL: {url[:80]}...")
            
            # グローバルのscraperを使用
            if use_cloudscraper and scraper:
                response = scraper.get(url, timeout=30, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.pokemon-zone.com/"
                })
            else:
                response = requests.get(url, timeout=30, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.pokemon-zone.com/"
                })
            
            response.raise_for_status()
            
            # レスポンスが画像かどうかをチェック
            content_type = response.headers.get('Content-Type', '')
            print(f"📄 コンテンツタイプ: {content_type}")
            
            if 'image' not in content_type:
                print(f"⚠️ 画像でないコンテンツを受信しました: {content_type}")
                print(f"⚠️ 受信したデータの先頭100バイト: {response.content[:100]}")
                
                # デバッグ用に受信データを保存
                debug_img_file = os.path.join(output_folder, f"debug_{filename}.txt")
                with open(debug_img_file, "wb") as f:
                    f.write(response.content[:500])  # 先頭500バイトだけ保存
                print(f"📝 デバッグデータを保存: {debug_img_file}")
                continue
            
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img = add_noise_and_crop(img)
            img.save(filepath, format="WEBP", quality=95)

            print(f"✅ ダウンロード & 処理完了: {filename}")
            seen_titles.discard(filename)  # 処理済みなので除外
            processed_count += 1
        except PermissionError as e:
            print(f"❌ ファイル書き込み権限エラー: {filename}")
            print(f"   エラー詳細: {e}")
            print(f"   ファイルパス: {filepath}")
            # 代替のファイル名を試す
            safe_filename = filename.replace('\n', '').replace('\r', '')
            safe_filepath = os.path.join(output_folder, safe_filename)
            try:
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = add_noise_and_crop(img)
                img.save(safe_filepath, format="WEBP", quality=95)
                print(f"✅ 代替ファイル名で保存成功: {safe_filename}")
                seen_titles.discard(filename)
                processed_count += 1
            except Exception as e2:
                print(f"❌ 代替保存も失敗: {e2}")
                seen_titles.discard(filename)
        except Exception as e:
            print(f"❌ {filename} の処理に失敗: {e}")
            import traceback
            traceback.print_exc()
            seen_titles.discard(filename)  # エラーでも除外

    print(f"📋 処理結果: {flair_titles}")
    print(f"📊 合計処理数: {processed_count}/{len(flair_data)}個の画像")
    return flair_titles
    
def get_card_info_from_limitless(card_number):
    """Limitless TCGからカード情報を取得する（完全版）"""
    try:
        set_code, card_id = card_number.split("#")
        original_set_code = set_code
        limitless_set = set_code.upper()
        
        # 汎用的な変換ルール
        # 1. プロモカード変換: PROMO-X → P-X
        if limitless_set.startswith("PROMO-"):
            limitless_set = limitless_set.replace("PROMO-", "P-")
        
        # 2. バーチャルパックの特殊ケース（数字 + アルファベットのパターン）
        # B2B → B2b, A1A → A1a など
        elif re.match(r'^[A-Z]\d[A-Z]$', limitless_set):  # 例: B2B, A1A
            limitless_set = limitless_set[0] + limitless_set[1] + limitless_set[2].lower()
        
        # 3. その他の変換が必要なケースがあればここに追加
        # elif limitless_set == "XXX":
        #     limitless_set = "xxx"
        
        if original_set_code != limitless_set:
            print(f"  🔄 セットコード変換: {original_set_code} → {limitless_set}")
            
        limitless_url = f"https://pocket.limitlesstcg.com/cards/{limitless_set}/{card_id}"
        
        # あなたの scrape_pocket_card の内容をここに
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(limitless_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        info = {}
        
        # 1. カード名・タイプ・HP
        title_elem = soup.select_one("p.card-text-title")
        if title_elem:
            text = ' '.join(title_elem.stripped_strings)
            # 「 - 」で分割（スペース+ハイフン+スペース）
            parts = [p.strip() for p in text.split(' - ')]
            info["名前"] = parts[0] if len(parts) > 0 else "N/A"
            info["タイプ"] = parts[1] if len(parts) > 1 else "N/A"
            hp_match = re.search(r'(\d+) HP', text)
            info["HP"] = hp_match.group(1) if hp_match else "N/A"
        
        # 2. ポケモン種類・進化ステージ
        type_elem = soup.select_one("p.card-text-type")
        if type_elem:
            text = ' '.join(type_elem.stripped_strings)
            if " - " in text:
                parts = text.split(" - ")
                info["カードの種類"] = parts[0].strip()
                info["進化ステージ"] = parts[1].strip()
            else:
                info["カードの種類"] = text.strip()
                info["進化ステージ"] = "N/A"
        
        # 3. ワザ情報
        attack_name_elem = soup.select_one("p.card-text-attack-info")
        attack_effect_elem = soup.select_one("p.card-text-attack-effect")
        
        attacks = []
        if attack_name_elem:
            attack_text = ' '.join(attack_name_elem.stripped_strings)
            match = re.match(r'^(\S+)\s+(.+?)\s*(\d+)$', attack_text)
            if match:
                energy = match.group(1)
                name = match.group(2)
                damage = match.group(3)
            else:
                match = re.match(r'^(\S+)\s+(.+)$', attack_text)
                if match:
                    energy = match.group(1)
                    name = match.group(2)
                    damage = "N/A"
                else:
                    energy, name, damage = "N/A", attack_text, "N/A"
            
            effect = ' '.join(attack_effect_elem.stripped_strings) if attack_effect_elem else "N/A"
            
            attacks.append({
                "名前": name,
                "ダメージ": damage,
                "効果": effect,
                "エネルギーコスト": len(energy),
                "エネルギータイプ": [energy.lower()] if energy != "N/A" else []
            })
        
        if attacks:
            info["ワザ"] = attacks
        
        # 4. 弱点・にげる
        wrr_elem = soup.select_one("p.card-text-wrr")
        if wrr_elem:
            lines = [line.strip() for line in wrr_elem.stripped_strings if line.strip()]
            for line in lines:
                if "Weakness:" in line:
                    info["弱点"] = line.replace("Weakness:", "").strip()
                elif "Retreat:" in line:
                    info["にげる"] = int(line.replace("Retreat:", "").strip())
        
        # 5. イラストレーター
        artist_elem = soup.select_one("div.card-text-artist")
        if artist_elem:
            text = ' '.join(artist_elem.stripped_strings)
            info["イラストレーター"] = text.replace("Illustrated by", "").strip()
        
        # 6. 説明文
        flavor_elem = soup.select_one("div.card-text-flavor")
        if flavor_elem:
            info["説明文"] = ' '.join(flavor_elem.stripped_strings)
        
        # 7. レア度
        prints_elem = soup.select_one(".prints-current-details")
        if prints_elem:
            raw_text = prints_elem.get_text()
            if '◇' in raw_text or '◊' in raw_text:
                info["レア度タイプ"] = "diamond"
            elif '☆' in raw_text:
                info["レア度タイプ"] = "star"
            elif '♛' in raw_text:
                info["レア度タイプ"] = "crown"
        
        print(f"✅ Limitless取得成功: {info.get('名前', 'Unknown')}")
        return info
        
    except Exception as e:
        print(f"❌ Limitlessエラー: {e}")
        return None
        
# -------- ファイル保存用必須関数 -------- #    
def sanitize_filename(filename):
    """Windowsや他のOSで使えない文字を安全な文字に置換"""
    # まずスペースを _ に変換
    filename = filename.replace(" ", "_")
    
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for ch in invalid_chars:
        filename = filename.replace(ch, '_')
    return filename
    
# -------- アクセス用デバッグ -------- # 
def debug_response(resp, url):
    print(f"\n{'='*50}")
    print(f"デバッグ情報: {url}")
    print(f"{'='*50}")
    
    print(f"📊 ステータスコード: {resp.status_code}")
    print(f"📏 コンテンツ長: {len(resp.content)} bytes")
    print(f"🔗 最終URL: {resp.url}")
    
    # 重要なヘッダーを表示
    important_headers = ['content-type', 'server', 'cf-ray', 'cf-challenge', 'set-cookie']
    print("📋 レスポンスヘッダー:")
    for header, value in resp.headers.items():
        if any(key in header.lower() for key in important_headers):
            print(f"  {header}: {value}")
    
    # ブロッキングチェック
    blocking_indicators = [
        ('cloudflare', 'Cloudflare検出'),
        ('access denied', 'アクセス拒否'),
        ('challenge', 'チャレンジページ'),
        ('captcha', 'CAPTCHA'),
        ('blocked', 'ブロック検出'),
        ('bot', 'ボット検出'),
    ]
    
    text_lower = resp.text.lower()
    print("🔍 ブロッキングチェック:")
    for keyword, message in blocking_indicators:
        if keyword in text_lower:
            print(f"  ⚠️ {message}")
    
    # レスポンス内容のプレビュー
    print("👀 レスポンスプレビュー:")
    if len(resp.text) > 500:
        print(resp.text[:250] + "..." + resp.text[-250:])
    else:
        print(resp.text)
    
    print(f"{'='*50}\n")
    
    # 成功判定
    return resp.status_code == 200 and len(resp.content) > 1000
    
# -------- アクセスのデバッグ -------- #
def debug_response(resp, url):
    print(f"\n{'='*50}")
    print(f"デバッグ情報: {url}")
    print(f"{'='*50}")
    
    print(f"📊 ステータスコード: {resp.status_code}")
    print(f"📏 コンテンツ長: {len(resp.content)} bytes")
    print(f"🔗 最終URL: {resp.url}")
    
    # 重要なヘッダーを表示
    important_headers = ['content-type', 'server', 'cf-ray', 'cf-challenge', 'set-cookie']
    print("📋 レスポンスヘッダー:")
    for header, value in resp.headers.items():
        if any(key in header.lower() for key in important_headers):
            print(f"  {header}: {value}")
    
    # ブロッキングチェック
    blocking_indicators = [
        ('cloudflare', 'Cloudflare検出'),
        ('access denied', 'アクセス拒否'),
        ('challenge', 'チャレンジページ'),
        ('captcha', 'CAPTCHA'),
        ('blocked', 'ブロック検出'),
        ('bot', 'ボット検出'),
    ]
    
    text_lower = resp.text.lower()
    print("🔍 ブロッキングチェック:")
    for keyword, message in blocking_indicators:
        if keyword in text_lower:
            print(f"  ⚠️ {message}")
    
    # レスポンス内容のプレビュー
    print("👀 レスポンスプレビュー:")
    if len(resp.text) > 500:
        print(resp.text[:250] + "..." + resp.text[-250:])
    else:
        print(resp.text)
    
    print(f"{'='*50}\n")
    
    # 成功判定
    return resp.status_code == 200 and len(resp.content) > 1000

def enhanced_request(url, headers, retry_count=3):
    """強化版リクエスト関数"""
    
    for attempt in range(retry_count + 1):
        try:
            # ... リクエスト処理 ...
            
            if use_cloudscraper and scraper:
                resp = scraper.get(url, headers=headers, timeout=40)
            else:
                session = requests.Session()
                resp = session.get(url, headers=headers, timeout=40)
            
            # レスポンスのサイズをチェック
            if len(resp.content) < 5000:
                print(f"⚠️ レスポンスが小さすぎます ({len(resp.content)} bytes)")
                print(f"   ブロックされている可能性があります")
                # デバッグ用に保存
                debug_file = f"debug_empty_{int(time.time())}.html"
                with open(debug_file, "wb") as f:
                    f.write(resp.content)
                print(f"   デバッグファイル保存: {debug_file}")
                
            # 403の場合は特別な処理
            if resp.status_code == 403:
                print(f"⚠️ 403検出 ({attempt+1}/{retry_count+1}回目リトライ)")
                if attempt < retry_count:
                    continue
            
            # チャレンジページかどうかをチェック
            if "Just a moment" in resp.text or "cloudflare" in resp.text.lower():
                print(f"⚠️ Cloudflareチャレンジページ検出 ({attempt+1}/{retry_count+1}回目リトライ)")
                if attempt < retry_count:
                    continue
            
            return resp
            
        except Exception as e:
            print(f"❌ リクエストエラー ({attempt+1}回目): {e}")
            if attempt < retry_count:
                continue
    
    return None
    
def smart_delay(last_response_time=None, consecutive_success=0, consecutive_fails=0):
    """
    レスポンス時間と成功率に基づいて賢く待機時間を決定
    
    Args:
        last_response_time: 最後のレスポンスにかかった時間（秒）
        consecutive_success: 連続成功回数
        consecutive_fails: 連続失敗回数
    
    Returns:
        float: 実際に待機した時間
    """
    
    base_delay = 10  # 基本待機時間
    
    # 連続失敗に応じて待機時間を増加
    if consecutive_fails > 0:
        base_delay = 30 * (2 ** min(consecutive_fails, 4))  # 指数関数的に増加（最大480秒）
        print(f"⚠️ 連続{consecutive_fails}回失敗のため待機時間延長: {base_delay}秒")
    
    # 連続成功に応じて少しずつ待機時間を短縮（ただし最低10秒）
    elif consecutive_success > 3:
        base_delay = max(10, base_delay - (consecutive_success - 3) * 2)
    
    # レスポンスが速すぎる場合はボットと判断される可能性があるので待機
    if last_response_time and last_response_time < 2:
        base_delay = max(base_delay, 20)  # 最低20秒
    
    # ランダム要素を追加（±20%）
    final_delay = base_delay * random.uniform(0.8, 1.2)
    
    print(f"⏳ スマート待機: {final_delay:.1f}秒 (基本: {base_delay}秒)")
    time.sleep(final_delay)
    
    return final_delay
    
# -------- 失敗URLの保存用関数 -------- #
def save_failed_urls(failed_urls, filename="失敗したurl.json"):
    """
    失敗したURLをJSONファイルに保存する
    
    Args:
        failed_urls (list): 失敗したURLのリスト
        filename (str): 保存するJSONファイル名
    """
    try:
        # 失敗したURLがない場合は空のリストを保存
        if not failed_urls:
            failed_urls = []
        
        # JSONファイルに保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(failed_urls, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 失敗したURLを保存しました: {filename} (件数: {len(failed_urls)})")
        
        # 失敗したURLを表示（デバッグ用）
        if failed_urls:
            print("📋 失敗したURL一覧:")
            for i, url in enumerate(failed_urls, 1):
                print(f"  {i}. {url}")
                
    except Exception as e:
        print(f"❌ 失敗URLの保存中にエラー: {e}")

# -------- Main -------- #
try:
    import cloudscraper
    use_cloudscraper = True
except ImportError:
    import requests
    use_cloudscraper = False
    print("[INFO] cloudscraperが使えないのでrequestsで代用します。")

# Cloudscraperインスタンスの作成
scraper = None
if use_cloudscraper:
    scraper = cloudscraper.create_scraper(
        delay=15,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'custom': '--disable-blink-features=AutomationControlled'
        }
    )

urls = get_urls_from_json("スクレイピングするカードurl.json")
    
# 訪問済みURLと失敗URLを追跡するセット
visited_cards = set()
failed_urls = []  # 失敗したURLを保存するリスト

# smart_delay用の変数
consecutive_success = 0
consecutive_fails = 0
last_response_time = None
max_consecutive_success = 0
max_consecutive_fails = 0

# メインループ開始
for i, url in enumerate(urls):
    print(f"\n{'='*60}")
    print(f"📋 処理中: {i+1}/{len(urls)} - {url}")
    print(f"{'='*60}")
    
    start_time = time.time()  # リクエスト開始時間を記録
    
    # smart_delayを使用した待機
    if i > 0:  # 最初のリクエスト以外はスマート待機
        print(f"📊 前回の状態: 連続成功={consecutive_success}, 連続失敗={consecutive_fails}")
        wait_time = smart_delay(
            last_response_time=last_response_time,
            consecutive_success=consecutive_success,
            consecutive_fails=consecutive_fails
        )
    else:
        # 最初のリクエストは短めの固定待機
        wait_time = random.uniform(5, 10)
        print(f"⏳ 初回待機: {wait_time:.1f}秒...")
        time.sleep(wait_time)
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Referer": "https://www.google.com/",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8,zh;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    # 強化版リクエストを使用
    resp = enhanced_request(url, headers)
    
    # レスポンス時間を計算
    response_time = time.time() - start_time
    last_response_time = response_time
    print(f"⏱️ レスポンス時間: {response_time:.2f}秒")
    
    if resp is None:
        print("❌ リクエストに失敗しました")
        consecutive_fails += 1
        consecutive_success = 0
        
        # 失敗したURLをリストに追加
        failed_urls.append(url)
        print(f"📝 失敗URLリストに追加: {url}")
        
        # 失敗した場合の追加対策
        print("🛑 失敗したため、次のURLまで長めに待機します")
        time.sleep(random.uniform(60, 120))
        continue
    
    # デバッグ情報を表示
    is_success = debug_response(resp, url)
    
    # 連続成功/失敗のカウントを更新
    if is_success:
        consecutive_success += 1
        consecutive_fails = 0
        print(f"✅ 連続成功: {consecutive_success}回目")
    else:
        consecutive_fails += 1
        consecutive_success = 0
        print(f"❌ 連続失敗: {consecutive_fails}回目")
        
        # 失敗したURLをリストに追加
        failed_urls.append(url)
        print(f"📝 失敗URLリストに追加: {url}")
    
    # 最大値の更新
    if consecutive_success > max_consecutive_success:
        max_consecutive_success = consecutive_success
    if consecutive_fails > max_consecutive_fails:
        max_consecutive_fails = consecutive_fails
    
    if is_success:
        soup = BeautifulSoup(resp.content, "html.parser")
        print("✅ 正常にページを処理しました")
        
        # 訪問済みとして記録
        visited_cards.add(url)
        
        # --- カード情報の取得 ---
        name = get_card_name(soup)
        rarity_counts = rarity_icons(soup)
        card_numbers = get_card_number(soup)  # ← ここに移動（早めに定義）
        image_url = get_card_image(soup)
        hp = get_hp(soup)
        poke_type = get_type(soup)
        weakness = get_weakness(soup)
        retreat_cost = get_retreat_cost(soup)
        description_data = get_card_description(soup)
        illustrator = get_illustrator(soup)
        series_packs, set_values = get_card_series_and_packs(soup, rarity_counts)
        abilities = get_abilities(soup)
        attacks = get_attacks(soup)
        alternate_arts = get_alternate_arts(soup)
        card_type, stage, unique_card_types = get_card_type_and_stage(soup, name, hp)
        card_effect = get_card_effect(soup)
        
        # ========== ここから追加（全取得後） ========== #
        # Limitless TCGから不足情報を補完
        limitless_info = None
        if card_numbers and card_numbers[0] != "N/A":
            # 関数を呼び出し
            limitless_info = get_card_info_from_limitless(card_numbers[0])
        
        # 取得した情報で不足を埋める
        if limitless_info:
            if name == "N/A" and limitless_info.get("名前"):
                name = limitless_info["名前"]
            if hp == "N/A" and limitless_info.get("HP"):
                hp = limitless_info["HP"]
            if poke_type == "N/A" and limitless_info.get("タイプ"):
                poke_type = limitless_info["タイプ"]
            if illustrator == "N/A" and limitless_info.get("イラストレーター"):
                illustrator = limitless_info["イラストレーター"]
            if card_type == "N/A" and limitless_info.get("カードの種類"):
                card_type = limitless_info["カードの種類"]
            if stage == "N/A" and limitless_info.get("進化ステージ"):
                stage = limitless_info["進化ステージ"]
            if weakness == "N/A" and limitless_info.get("弱点"):
                weakness = limitless_info["弱点"]
            if retreat_cost == 0 and limitless_info.get("にげる"):
                retreat_cost = limitless_info["にげる"]
            if not description_data.get("説明文") and limitless_info.get("説明文"):
                description_data["説明文"] = limitless_info["説明文"]
            if not abilities and limitless_info.get("特性"):
                abilities = limitless_info["特性"]
            if not attacks and limitless_info.get("ワザ"):
                attacks = limitless_info["ワザ"]
            
            print(f"✅ Limitless補完完了: {name}")
            
            # 特別ルールの判定（名前から）
            unique_card_types_from_name = []
            name_lower = name.lower()
            
            if name_lower.startswith("mega "):
                unique_card_types_from_name.append("Mega")
            
            if " ex" in name_lower:
                unique_card_types_from_name.append("ex")
            
            if unique_card_types_from_name:
                # 既存の unique_card_types があればマージ
                if unique_card_types:
                    unique_card_types = list(set(unique_card_types + unique_card_types_from_name))
                else:
                    unique_card_types = unique_card_types_from_name
                print(f"✨ 特別ルール判定: {unique_card_types}")
                
        # --- Flair画像の取得（エラーハンドリング付き）---
        effect_text = []
        try:
            effect_text = get_flair_titles(soup)
            print(f"🎨 Flair画像処理完了: {len(effect_text)}個の画像を処理")
        except Exception as e:
            print(f"❌ Flair取得中にエラー: {e}")
            import traceback
            traceback.print_exc()
            effect_text = []
        
        # --- 進化情報の取得 ---
        ev_into_dict = {}
        ev_from_dict = {}
        
        if card_type == "Pokémon":
            fetch_ev_into(soup, ev_into_dict)
            fetch_ev_from(soup, ev_from_dict)
        else:
            fetch_ev_into(soup, ev_from_dict)
            
        # --- データ整形 ---
        if card_type == "Pokémon":
            data = {
                "カードの種類": card_type,
                "カード番号": card_numbers,
                "名前": name,
                "レア度": rarity_counts,
                "HP": hp,
                "タイプ": poke_type,
                "弱点": weakness,
                "にげる": retreat_cost,
                "説明文": description_data.get("説明文", ""),
                "イラストレーター": illustrator,
                "収録セット": set_values,
                "入手方法": series_packs,
                "進化ステージ": stage,
                "特別ルール": unique_card_types,
                "エフェクト一覧": effect_text,
                "特性": [
                    {"特性名": ability["name"], "効果": ability["effect"]}
                    for ability in abilities
                ],
                "ワザ": [
                    {
                        "名前": attack["name"],
                        "ダメージ": attack["damage"],
                        "効果": attack["effect"],
                        "エネルギーコスト": attack["energy_cost"],
                        "エネルギータイプ": attack["energy_types"]
                    }
                    for attack in attacks
                ],
                "Alternate Arts": [
                    {"カード番号": alt_card_num}
                    for alt_card_num in (alternate_arts or [])
                ],
                "進化先": {
                    str(depth): names for depth, names in sorted(ev_into_dict.items())
                },
                "進化前": {
                    str(depth): names for depth, names in sorted(ev_from_dict.items())
                }
            }
        else:
            data = {
                "カードの種類": card_type,
                "カード番号": card_numbers,
                "レア度": rarity_counts,
                "HP": hp,
                "名前": name,
                "イラストレーター": illustrator,
                "収録セット": set_values,
                "入手方法": series_packs,
                "分類": stage,
                "カードの効果": card_effect,
                "エフェクト効果": effect_text,
                "Alternate Arts": [
                    {"カード番号": card_num}
                    for card_num in (alternate_arts or [])
                ],
                "進化先": {
                    str(depth): names for depth, names in sorted(ev_from_dict.items())
                }
            }

        # ---カードごとのフォルダを作成 ---
        if card_numbers == ["N/A"] or not card_numbers:
            print(f"⚠️ カード番号が取得できませんでした: {name}")
        else:
            for card_number in card_numbers:
                try:
                    set_code, card_no = card_number.split("#")
                    save_dir = os.path.join("..", "..", "スクレイピングデータ", "cards_json", set_code, card_no)
                    os.makedirs(save_dir, exist_ok=True)

                    # --- 名前をファイル名に変換 ---
                    safe_name = sanitize_filename(name)
                    json_path = os.path.join(save_dir, f"{safe_name}.json")

                    # --- JSONファイルとして保存 ---
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    print(f"✅ {name} のデータを保存しました: {json_path}")
                    
                except Exception as e:
                    print(f"❌ データ保存中にエラーが発生しました: {name} - {card_number}\n{e}")
        
    else:
        print("❌ このURLの処理をスキップします")
        
        # 失敗した場合の追加対策
        if "cloudflare" in resp.text.lower():
            print("🛡️ Cloudflare検出 - 次のリクエストまで長めに待機")
            time.sleep(random.uniform(60, 120))
        
        continue

print(f"\n{'='*60}")
print(f"🎉 処理完了: {len(visited_cards)}/{len(urls)} 個のページを正常に処理しました")
print(f"📊 最終統計: 連続成功最大={max_consecutive_success}, 連続失敗最大={max_consecutive_fails}")
print(f"❌ 失敗件数: {len(failed_urls)}")

# 失敗したURLをJSONファイルに保存
save_failed_urls(failed_urls, "失敗したurl.json")
print(f"{'='*60}\n")