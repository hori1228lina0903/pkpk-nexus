import os
import json
import time
import random
import re
import hashlib
from bs4 import BeautifulSoup
import cloudscraper
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from PIL import Image, ImageFilter, ImageChops
import numpy as np
from io import BytesIO

# -------- 設定 --------
JSON_PATH = '/storage/emulated/0/html/pkpk/py/イベントhtml生成py/スクレイピングするイベントurl.json'
BASE_OUTPUT_DIR = '/storage/emulated/0/html/pkpk/Events'
PROGRESS_FILE = '/storage/emulated/0/html/pkpk/イベント取得_progress.json'
FAILED_URLS_FILE = '/storage/emulated/0/html/pkpk/イベント取得_失敗.json'
EMBLEM_IMAGE_DIR = '/storage/emulated/0/html/pkpk/images/emblem'
UNPROCESSED_EVENTS_FILE = '/storage/emulated/0/html/pkpk/未処理イベント.json'
TICKET_IMAGE_DIR = '/storage/emulated/0/html/pkpk/images/tickets'
DECK_IMAGE_DIR = '/storage/emulated/0/html/pkpk/images/decks'

# 画像保存設定
IMAGE_QUALITY = 80
IMAGE_FORMAT = 'WEBP'

# イベントタイプ判定用キーワード
DROP_KEYWORDS = ['Drop Event', 'drop event', 'Drop', 'drop']
WONDER_PICK_KEYWORDS = ['Wonder Pick', 'Wonder pick', 'wonder pick', 'Wonderpick']
MASS_OUTBREAK_KEYWORDS = ['Mass Outbreak', 'mass outbreak', 'Mass Outbreak Wonder Pick']
RANKED_MATCH_KEYWORDS = ['Ranked Match', 'ranked match', 'Ranked', 'ranked']
EMBLEM_EVENT_KEYWORDS = ['Emblem Event', 'emblem event', 'Emblem', 'emblem']
RELEASE_KEYWORDS = ['release', 'Release', 'リリース']
PREMIUM_SHOP_KEYWORDS = ['Premium Shop', 'premium shop', 'Premium Shop Lineup']

# -------- Cloudscraperの設定 --------
try:
    scraper = cloudscraper.create_scraper(
        delay=15,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True,
        },
        interpreter='nodejs',
        captcha={
            'provider': 'return_response',
        }
    )
    print("✅ cloudscraperを初期化しました")
except Exception as e:
    print(f"❌ cloudscraper初期化エラー: {e}")
    scraper = requests.Session()
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    })

# -------- User-Agentリスト --------
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
]


# -------- 画像処理関数 --------
def trim_transparent_border(image):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    alpha = image.getchannel('A')
    bbox = alpha.getbbox()
    if bbox:
        bbox = (bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1)
        if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
            image = image.crop(bbox)
    return image

def add_noise_to_non_transparent(image, noise_level=10):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    img_array = np.array(image)
    alpha_mask = img_array[:, :, 3] > 0
    noise = np.random.randint(-noise_level, noise_level + 1, img_array[:, :, :3].shape)
    noisy_rgb = img_array[:, :, :3].astype(np.int16) + noise
    noisy_rgb = np.clip(noisy_rgb, 0, 255).astype(np.uint8)
    img_array[:, :, :3] = np.where(alpha_mask[:, :, np.newaxis], noisy_rgb, img_array[:, :, :3])
    return Image.fromarray(img_array, 'RGBA')

def process_emblem_image(image_data):
    try:
        img = Image.open(BytesIO(image_data)).convert('RGBA')
        img = trim_transparent_border(img)
        img = add_noise_to_non_transparent(img)
        output = BytesIO()
        img.save(output, format=IMAGE_FORMAT, quality=IMAGE_QUALITY, method=6, lossless=False)
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"⚠️ 画像処理エラー: {e}")
        return image_data

def download_emblem_image(img_url, emblem_name, index=0):
    try:
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = urljoin('https://www.pokemon-zone.com', img_url)
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', emblem_name)
        filename = f"{safe_name}.webp"
        filepath = os.path.join(EMBLEM_IMAGE_DIR, filename)
        if os.path.exists(filepath):
            print(f"   ⏩ 画像既存: {filename}")
            return filename
        print(f"   🖼️ 画像DL: {img_url}")
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.pokemon-zone.com/",
        }
        resp = scraper.get(img_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            processed_image_data = process_emblem_image(resp.content)
            with open(filepath, 'wb') as f:
                f.write(processed_image_data)
            print(f"   ✅ 保存: {filename}")
            return filename
        else:
            print(f"   ⚠️ DL失敗: {resp.status_code}")
            return None
    except Exception as e:
        print(f"   ⚠️ DLエラー: {e}")
        return None

def download_ticket_image(img_url, ticket_name, index=0):
    try:
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = urljoin('https://www.pokemon-zone.com', img_url)
        clean_name = re.sub(r'^\d+x\s+', '', ticket_name)
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name)
        filename = f"{safe_name}.webp"
        filepath = os.path.join(TICKET_IMAGE_DIR, filename)
        if os.path.exists(filepath):
            return filename
        print(f"   🎫 チケットDL: {img_url}")
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.pokemon-zone.com/",
        }
        resp = scraper.get(img_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            processed_image_data = process_emblem_image(resp.content)
            with open(filepath, 'wb') as f:
                f.write(processed_image_data)
            print(f"   ✅ チケット保存: {filename}")
            return filename
        return None
    except Exception as e:
        print(f"   ⚠️ チケットDLエラー: {e}")
        return None
        
def fetch_page(url, retry_count=5):
    for attempt in range(retry_count):
        try:
            if attempt == 0:
                wait_time = 30
                print(f"⏳ 初回待機: {wait_time}秒...")
                time.sleep(wait_time)
            elif attempt > 0:
                wait_time = 30 * (2 ** (attempt - 1))
                print(f"🔄 リトライ {attempt+1}/{retry_count}: {wait_time}秒待機...")
                time.sleep(wait_time)
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Referer": "https://www.google.com/",
            }
            print(f"🌐 取得中: {url}")
            resp = scraper.get(url, headers=headers, timeout=45)
            if resp.status_code == 200:
                if len(resp.text) < 500:
                    print("⚠️ HTMLが短すぎます")
                    continue
                if "Just a moment" in resp.text or "Checking your browser" in resp.text:
                    print("⚠️ Cloudflareチャレンジ検出")
                    continue
                return resp
            else:
                print(f"⚠️ ステータスコード: {resp.status_code}")
        except Exception as e:
            print(f"❌ エラー: {e}")
        if attempt < retry_count - 1:
            continue
    return None

def sanitize_filename(filename):
    filename = filename.replace(" ", "_")
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '#', '%', '&', '{', '}']
    for ch in invalid_chars:
        filename = filename.replace(ch, '_')
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')

def get_event_type_from_title(title):
    title_lower = title.lower()
    if any(kw.lower() in title_lower for kw in PREMIUM_SHOP_KEYWORDS):
        return "premium_shop"
    elif any(kw.lower() in title_lower for kw in MASS_OUTBREAK_KEYWORDS):
        return "mass_outbreak"
    elif any(kw.lower() in title_lower for kw in RANKED_MATCH_KEYWORDS):
        return "ranked_match"
    elif any(kw.lower() in title_lower for kw in EMBLEM_EVENT_KEYWORDS):
        return "emblem_event"
    elif any(kw.lower() in title_lower for kw in DROP_KEYWORDS):
        return "drop_event"
    elif any(kw.lower() in title_lower for kw in WONDER_PICK_KEYWORDS):
        return "wonder_pick"
    elif any(kw.lower() in title_lower for kw in RELEASE_KEYWORDS):
        return "release"
    return "other"
    
def extract_pick_combinations(section, pick_type, soup):
    picks = []
    tabs = section.find_all('button', class_=re.compile(r'button--size-sm'))
    if not tabs:
        tabs = section.find_all('button', attrs={'role': 'tab'})
    if not tabs:
        return picks
    for tab in tabs:
        percent_text = tab.get_text(strip=True)
        percent_match = re.search(r'(\d+)%', percent_text)
        percent = int(percent_match.group(1)) if percent_match else 0
        target_id = tab.get('data-tab-target', '') or tab.get('data-bs-target', '')
        if target_id:
            panel_id = target_id.lstrip('#')
            panel = soup.find(id=panel_id)
            if panel:
                pick_data = extract_wonder_pick_card(panel, pick_type, percent)
                if pick_data:
                    picks.append(pick_data)
    return picks

def extract_wonder_pick_card(panel, pick_type, percent):
    items = []
    choices = panel.find_all('div', class_='wonder-pick-card__choice')
    for choice in choices:
        item_div = choice.find('div', class_='wonder-pick-card__item')
        if item_div:
            title = item_div.get('data-bs-original-title', '') or item_div.get('title', '')
            preview = item_div.find('span', class_='common-item-preview')
            if preview:
                style = preview.get('style', '')
                url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                img_url = url_match.group(1) if url_match else ""
                count_span = item_div.find('div', class_='wonder-pick-card__item-count')
                count = count_span.text.strip() if count_span else "1"
                items.append({
                    "type": "item",
                    "name": title,
                    "image_url": img_url,
                    "count": count
                })
        elif choice.find('a', href=True):
            link = choice.find('a')
            href = link.get('href', '')
            img = link.find('img')
            alt = img.get('alt', '') if img else ""
            card_name = alt.split(' - ')[0].strip() if alt else ""
            match = re.search(r'/cards/([^/]+/\d+)/', href)
            card_id = match.group(1) if match else href
            items.append({
                "type": "card",
                "name": card_name,
                "full_name": alt,
                "url": href,
                "id": card_id
            })
    cost = 0
    cost_free = False
    cost_div = panel.find('div', class_='wonder-pick-card__cost')
    if cost_div:
        free_div = cost_div.find('div', class_='wonder-pick-card__cost-free')
        if free_div:
            cost_free = True
        else:
            amount_span = cost_div.find('div', class_='wonder-pick-card__cost-amount')
            if amount_span:
                cost = int(amount_span.text.strip())
    return {
        "type": pick_type,
        "percent": percent,
        "items": items,
        "cost": 0 if cost_free else cost,
        "cost_free": cost_free
    }
    
def extract_ranked_match_details(soup, url):
    os.makedirs(EMBLEM_IMAGE_DIR, exist_ok=True)
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    set_name = ""
    set_match = re.search(r'\(([A-Za-z0-9]+)\)', title)
    if set_match:
        set_name = set_match.group(1)
        print(f"   🔖 セット名: {set_name}")
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    ranks = []
    rank_tables = soup.find_all('table')
    category_mapping = {
        'ビギナー': 'Beginner',
        'モンスターボール': 'Poké Ball',
        'スーパーボール': 'Great Ball',
        'ハイパーボール': 'Ultra Ball',
        'マスターボール': 'Master Ball'
    }
    for table in rank_tables:
        rank_category = ""
        prev_h3 = table.find_previous('h3')
        if prev_h3:
            category_text = prev_h3.text.strip()
            rank_category = category_mapping.get(category_text, category_text)
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                rank_cell = cells[0]
                rank_span = rank_cell.find('span', class_='badge')
                rank_text = rank_span.text.strip() if rank_span else rank_cell.text.strip()
                emblem_name = ""
                if 'ビギナー' in rank_text or 'Beginner' in rank_text:
                    num_match = re.search(r'(\d+)', rank_text)
                    rank_num = num_match.group(1) if num_match else "1"
                    emblem_name = f"Season {set_name} Beginner Rank {rank_num}"
                elif 'モンスターボール' in rank_text or 'Poké Ball' in rank_text:
                    num_match = re.search(r'(\d+)', rank_text)
                    rank_num = num_match.group(1) if num_match else "1"
                    emblem_name = f"Season {set_name} Poké Ball Rank {rank_num}"
                elif 'スーパーボール' in rank_text or 'Great Ball' in rank_text:
                    num_match = re.search(r'(\d+)', rank_text)
                    rank_num = num_match.group(1) if num_match else "1"
                    emblem_name = f"Season {set_name} Great Ball Rank {rank_num}"
                elif 'ハイパーボール' in rank_text or 'Ultra Ball' in rank_text:
                    num_match = re.search(r'(\d+)', rank_text)
                    rank_num = num_match.group(1) if num_match else "1"
                    emblem_name = f"Season {set_name} Ultra Ball Rank {rank_num}"
                elif 'マスターボール' in rank_text or 'Master Ball' in rank_text:
                    rank_text_lower = rank_text.lower()
                    if 'top 10000' in rank_text_lower:
                        emblem_name = f"Season {set_name} Master Ball Rank (TOP 10,000)"
                    elif 'top 5000' in rank_text_lower:
                        emblem_name = f"Season {set_name} Master Ball Rank (TOP 5,000)"
                    elif 'top 1000' in rank_text_lower:
                        emblem_name = f"Season {set_name} Master Ball Rank (TOP 1,000)"
                    else:
                        emblem_name = f"Season {set_name} Master Ball Rank (Unranked)"
                emblem_data = None
                if len(cells) >= 2:
                    emblem_cell = cells[1]
                    emblem_span = emblem_cell.find('span', class_='common-item-icon')
                    if emblem_span:
                        preview_span = emblem_span.find('span', class_='common-item-preview')
                        if preview_span:
                            style = preview_span.get('style', '')
                            url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                            if url_match:
                                img_url = url_match.group(1)
                                filename = download_emblem_image(img_url, emblem_name, len(ranks))
                                if filename:
                                    emblem_data = {
                                        "name": emblem_name,
                                        "local_file": filename,
                                        "url": img_url
                                    }
                reward_data = None
                if len(cells) >= 3:
                    reward_cell = cells[2]
                    reward_span = reward_cell.find('span', class_='common-item-icon')
                    if reward_span:
                        reward_name = reward_span.get('title', '')
                        amount_span = reward_span.find('span', class_='common-item-icon__amount')
                        amount = amount_span.text.strip() if amount_span else ""
                        reward_data = {"name": reward_name, "amount": amount}
                if emblem_data or rank_text:
                    rank_info = {"category": rank_category, "rank": rank_text, "emblem": emblem_data}
                    if reward_data:
                        rank_info["reward"] = reward_data
                    ranks.append(rank_info)
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "set_name": set_name,
        "ranks": ranks
    }
    
def extract_emblem_event_details(soup, url):
    os.makedirs(EMBLEM_IMAGE_DIR, exist_ok=True)
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    emblems = []
    emblem_table = soup.find('table')
    if emblem_table:
        emblem_spans = emblem_table.find_all('span', class_='common-item-icon')
        for idx, emblem_span in enumerate(emblem_spans):
            original_name = emblem_span.get('title', f'Emblem_{idx}')
            emblem_name = original_name.strip()
            preview_span = emblem_span.find('span', class_='common-item-preview')
            if preview_span:
                style = preview_span.get('style', '')
                url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                if url_match:
                    img_url = url_match.group(1)
                    filename = download_emblem_image(img_url, emblem_name, idx)
                    if filename:
                        emblems.append({
                            "name": emblem_name,
                            "local_file": filename,
                            "url": img_url,
                            "position": idx,
                            "condition": ""
                        })
        body_row = emblem_table.find('tbody')
        if body_row and emblems:
            td_cells = body_row.find_all('td')
            for idx, td in enumerate(td_cells):
                if idx < len(emblems):
                    condition_text = td.get_text(separator=' ', strip=True)
                    emblems[idx]["condition"] = condition_text
    missions = []
    mission_groups = soup.find_all('div', class_='mission-group')
    for group in mission_groups:
        group_name_elem = group.find('div', class_='mission-group__name')
        group_name = group_name_elem.text.strip() if group_name_elem else ""
        group_date = group.find('span', class_='banner-date__dates')
        date_text = group_date.text.strip() if group_date else ""
        mission_list = []
        mission_cards = group.find_all('div', class_='mission-list-card')
        for card in mission_cards:
            text_elem = card.find('div', class_='mission-list-card__text')
            mission_text = text_elem.text.strip() if text_elem else ""
            reward_data = None
            preview_div = card.find('div', class_='mission-list-card__preview')
            if preview_div:
                reward_span = preview_div.find('span', class_='common-item-icon')
                if reward_span:
                    reward_name = reward_span.get('title', '')
                    amount_span = reward_span.find('span', class_='common-item-icon__amount')
                    amount = amount_span.text.strip() if amount_span else ""
                    reward_data = {"name": reward_name, "amount": amount}
            if mission_text:
                mission_list.append({"description": mission_text, "reward": reward_data})
        if mission_list:
            missions.append({"name": group_name, "period": date_text, "missions": mission_list})
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "emblems": emblems,
        "missions": missions
    }
    
def extract_drop_event_details(soup, url):
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    promo_pack = {"name": "", "cards": []}
    pack_section = soup.find('div', class_='event-details__packs')
    if pack_section:
        pack_title = pack_section.find('h3')
        if pack_title:
            promo_pack["name"] = pack_title.text.strip()
        card_cells = pack_section.find_all('div', class_='card-grid__cell')
        for cell in card_cells:
            card_link = cell.find('a', href=True)
            if card_link and '/cards/' in card_link['href']:
                card_url = card_link['href']
                caption = cell.find('figcaption', class_='card-grid__cell-card-caption')
                card_name = caption.text.strip() if caption else ""
                if card_name:
                    promo_pack["cards"].append({"name": card_name, "url": card_url})
    battles = []
    battle_groups = soup.find_all('div', class_='solo-battle-group-card')
    for group in battle_groups:
        difficulty_elem = group.find('span', class_='solo-battle-group-card__difficulty')
        if not difficulty_elem:
            continue
        difficulty = difficulty_elem.text.strip()
        deck_type = "Unknown"
        if group.find('div', class_='solo-battle-group-card__battle--type-Water'):
            deck_type = "Water"
        tasks = []
        task_elements = group.find_all('div', class_='solo-battle-group-card__challenge')
        for task_elem in task_elements:
            task_text_elem = task_elem.find('div', class_='solo-battle-group-card__challenge-text')
            if task_text_elem:
                task_text = task_text_elem.text.strip()
                if task_text:
                    tasks.append(task_text)
        battles.append({"difficulty": difficulty, "deck_type": deck_type, "tasks": tasks})
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "promo_pack": promo_pack,
        "battles": battles
    }
    
def extract_wonder_pick_details(soup, url):
    os.makedirs(TICKET_IMAGE_DIR, exist_ok=True)
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    
    # プロモカード情報
    promo_cards = []
    card_links = soup.select('a[href^="/cards/"]')
    for link in card_links:
        href = link.get('href', '')
        if '/promo-' in href:
            img = link.find('img')
            card_name = ""
            if img and img.get('alt'):
                alt_text = img.get('alt')
                card_name = alt_text.split(' - ')[0].strip()
            match = re.search(r'/cards/([^/]+/\d+)/', href)
            card_id = match.group(1) if match else href
            set_match = re.search(r'/promo-([a-z]+)/', href)
            set_name = f"promo-{set_match.group(1)}" if set_match else "promo"
            promo_cards.append({
                "name": card_name,
                "full_name": img.get('alt', '') if img else '',
                "url": href,
                "id": card_id,
                "set": set_name
            })
    
    # 重複除去
    unique_cards = []
    seen_urls = set()
    seen_names = set()
    for card in promo_cards:
        if card['url'] not in seen_urls:
            if card['name'] not in seen_names:
                seen_urls.add(card['url'])
                seen_names.add(card['name'])
                unique_cards.append(card)
            else:
                for existing in unique_cards:
                    if existing['name'] == card['name']:
                        if 'alternative_urls' not in existing:
                            existing['alternative_urls'] = []
                        existing['alternative_urls'].append(card['url'])
                        break
    
    # Bonus Pick抽出
    bonus_picks = []
    bonus_sections = soup.find_all('div', class_='event-details__picks') + soup.find_all('div', class_='event_details__picks')
    for section in bonus_sections:
        if 'Bonus Pick' in section.get_text():
            picks_data = extract_pick_combinations(section, 'bonus', soup)
            for pick in picks_data:
                for item in pick.get('items', []):
                    if item.get('type') == 'item':
                        item_name = item.get('name', '')
                        img_url = item.get('image_url', '')
                        if 'ticket' in item_name.lower() or 'SHOPTICKET' in img_url:
                            download_ticket_image(img_url, item_name)
            if picks_data:
                bonus_picks.extend(picks_data)
    
    # Chansey/Rare Pick抽出
    rare_picks = []
    rare_sections = soup.find_all('div', class_='event-details__picks') + soup.find_all('div', class_='event_details__picks')
    for section in rare_sections:
        if 'Chansey Pick' in section.get_text() or 'Rare Pick' in section.get_text():
            pick_type = 'chansey' if 'Chansey Pick' in section.get_text() else 'rare'
            picks_data = extract_pick_combinations(section, pick_type, soup)
            for pick in picks_data:
                for item in pick.get('items', []):
                    if item.get('type') == 'item':
                        item_name = item.get('name', '')
                        img_url = item.get('image_url', '')
                        if 'ticket' in item_name.lower() or 'SHOPTICKET' in img_url:
                            download_ticket_image(img_url, item_name)
            if picks_data:
                rare_picks.extend(picks_data)
    
    # ショップアイテム抽出
    shop_items = []
    shop_sections = soup.find_all('div', class_='shop-group-card')
    for section in shop_sections:
        section_title = section.find('h3')
        title_text = section_title.text.strip() if section_title else ""
        section_date = section.find('span', class_='banner-date__dates')
        date_text = section_date.text.strip() if section_date else ""
        items = []
        item_elements = section.find_all('div', class_='shop-group-card__item')
        for item in item_elements:
            name_elem = item.find('div', class_='shop-group-card__content-name')
            item_name = name_elem.text.strip() if name_elem else ""
            item_name = item_name.replace('\n', '').strip()
            price_bar = item.find('div', class_='product-price-bar')
            price = ""
            currency = ""
            if price_bar:
                price_elem = price_bar.find('div', class_='product-price-bar__price')
                price = price_elem.text.strip() if price_elem else ""
                title_attr = price_bar.get('title', '') or price_bar.get('data-bs-original-title', '')
                if title_attr:
                    currency = re.sub(r'^\d+x\s+', '', title_attr)
                else:
                    style = price_bar.get('style', '')
                    url_match = re.search(r'url\([^)]*/([^/]+)\.webp', style)
                    if url_match:
                        currency = url_match.group(1)
            tooltip = item.find('div', class_='shop-group-card__content')
            description = tooltip.get('title', '') if tooltip else ""
            if item_name and price:
                items.append({
                    "name": item_name,
                    "description": description,
                    "price": price,
                    "currency": currency
                })
        if items:
            shop_items.append({"title": title_text, "period": date_text, "items": items})
    
    # ミッション抽出
    missions = []
    mission_groups = soup.find_all('div', class_='mission-group')
    for group in mission_groups:
        group_name_elem = group.find('div', class_='mission-group__name')
        group_name = group_name_elem.text.strip() if group_name_elem else ""
        group_date = group.find('span', class_='banner-date__dates')
        date_text = group_date.text.strip() if group_date else ""
        mission_list = []
        mission_cards = group.find_all('div', class_='mission-list-card')
        for card_index, card in enumerate(mission_cards):
            text_elem = card.find('div', class_='mission-list-card__text')
            mission_text = text_elem.text.strip() if text_elem else ""
            all_rewards = []
            preview_div = card.find('div', class_='mission-list-card__preview')
            if preview_div:
                reward_spans = preview_div.find_all('span', class_='common-item-icon')
                for reward_span in reward_spans:
                    reward_name = reward_span.get('title', '')
                    amount_span = reward_span.find('span', class_='common-item-icon__amount')
                    amount = amount_span.text.strip() if amount_span else "1"
                    preview_span = reward_span.find('span', class_='common-item-preview')
                    if preview_span:
                        style = preview_span.get('style', '')
                        url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        if url_match:
                            img_url = url_match.group(1)
                            if 'ticket' in img_url.lower() or 'EVENT_SHOPTICKET' in img_url or 'SHOPTICKET' in img_url:
                                filename = download_ticket_image(img_url, reward_name, card_index)
                            else:
                                filename = None
                            all_rewards.append({
                                "name": reward_name,
                                "local_file": filename,
                                "url": img_url,
                                "amount": amount,
                                "type": "main"
                            })
            rewards_div = card.find('div', class_='mission-list-card__rewards')
            if rewards_div:
                icon_list = rewards_div.find('div', class_='icon-list')
                if icon_list:
                    sub_reward_spans = icon_list.find_all('span', class_='common-item-icon')
                    for sub_reward in sub_reward_spans:
                        sub_name = sub_reward.get('title', '')
                        preview = sub_reward.find('span', class_='common-item-preview')
                        if preview and sub_name:
                            style = preview.get('style', '')
                            url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                            if url_match:
                                sub_img_url = url_match.group(1)
                                amount_span = sub_reward.find('span', class_='common-item-icon__amount')
                                amount = amount_span.text.strip() if amount_span else "1"
                                if 'ticket' in sub_img_url.lower() or 'EVENT_SHOPTICKET' in sub_img_url or 'SHOPTICKET' in sub_img_url:
                                    sub_filename = download_ticket_image(sub_img_url, sub_name, card_index)
                                else:
                                    sub_filename = None
                                all_rewards.append({
                                    "name": sub_name,
                                    "local_file": sub_filename,
                                    "url": sub_img_url,
                                    "amount": amount,
                                    "type": "sub"
                                })
            progress_text = ""
            progress_bar = card.find('div', class_='progress-bar__text')
            if progress_bar:
                progress_text = progress_bar.text.strip()
            if mission_text:
                mission_item = {"description": mission_text}
                if all_rewards:
                    mission_item["rewards"] = all_rewards
                if progress_text:
                    mission_item["target"] = progress_text
                mission_list.append(mission_item)
        if mission_list:
            missions.append({"name": group_name, "period": date_text, "missions": mission_list})
    
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "promo_cards": unique_cards,
        "shop_items": shop_items,
        "missions": missions,
        "bonus_picks": bonus_picks,
        "rare_picks": rare_picks
    }
    
def extract_mass_outbreak_details(soup, url):
    os.makedirs(TICKET_IMAGE_DIR, exist_ok=True)
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    target_type = ""
    type_match = re.search(r'(\w+)-Type Mass Outbreak', title, re.IGNORECASE)
    if type_match:
        target_type = type_match.group(1)
    
    bonus_picks = []
    rare_picks = []
    exclusive_flair = []
    
    # Bonus Pick抽出
    bonus_sections = soup.find_all('div', class_='event-details__picks') + soup.find_all('div', class_='event_details__picks')
    for section in bonus_sections:
        if 'Bonus Pick' in section.get_text():
            picks_data = extract_pick_combinations(section, 'bonus', soup)
            if picks_data:
                bonus_picks.extend(picks_data)
    
    # Rare Pick抽出
    rare_sections = soup.find_all('div', class_='event_details__picks') + soup.find_all('div', class_='event-details__picks')
    for section in rare_sections:
        if 'Rare Pick' in section.get_text() or 'rare pick' in section.get_text().lower():
            picks_data = extract_pick_combinations(section, 'rare', soup)
            if picks_data:
                rare_picks.extend(picks_data)
    
    # Exclusive Flair抽出
    flair_section = soup.find('div', class_='event_details__flairs')
    if not flair_section:
        flair_section = soup.find('div', class_='event-details__flairs')
    if flair_section:
        flair_items = flair_section.find_all('div', class_='skin-image')
        if not flair_items:
            flair_items = flair_section.find_all('span', class_='common-item-icon')
        for flair in flair_items:
            flair_name = ""
            tooltip_elem = flair.find('span', class_='common-item-icon') if flair.name == 'div' else flair
            if tooltip_elem:
                flair_name = tooltip_elem.get('title', '')
            else:
                flair_name = flair.get('title', '')
            img_url = ""
            preview = flair.find('span', class_='common-item-preview')
            if preview:
                style = preview.get('style', '')
                url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                if url_match:
                    img_url = url_match.group(1)
            requirements = []
            price_bars = flair_section.find_all('div', class_='product-price-bar')
            for price_bar in price_bars:
                tooltip = price_bar.get('title', '') or price_bar.get('data-bs-original-title', '')
                price_elem = price_bar.find('div', class_='product-price-bar__price')
                price_text = price_elem.text.strip() if price_elem else ""
                style = price_bar.get('style', '')
                icon_match = re.search(r'url\([^)]*/([^/]+)\.webp', style)
                icon_name = icon_match.group(1) if icon_match else ""
                if tooltip or price_text:
                    requirements.append({
                        "item": tooltip if tooltip else icon_name,
                        "amount": price_text,
                        "icon": icon_name
                    })
            flair_date = flair_section.find('span', class_='banner-date__dates')
            date_text = flair_date.text.strip() if flair_date else ""
            if flair_name:
                exclusive_flair.append({
                    "name": flair_name,
                    "image_url": img_url,
                    "requirements": requirements,
                    "period": date_text
                })
    
    # ミッション抽出
    missions = []
    mission_groups = soup.find_all('div', class_='mission-group')
    for group in mission_groups:
        group_name_elem = group.find('div', class_='mission-group__name')
        group_name = group_name_elem.text.strip() if group_name_elem else ""
        group_date = group.find('span', class_='banner-date__dates')
        date_text = group_date.text.strip() if group_date else ""
        mission_list = []
        mission_cards = group.find_all('div', class_='mission-list-card')
        for card_index, card in enumerate(mission_cards):
            text_elem = card.find('div', class_='mission-list-card__text')
            mission_text = text_elem.text.strip() if text_elem else ""
            all_rewards = []
            preview_div = card.find('div', class_='mission-list-card__preview')
            if preview_div:
                reward_spans = preview_div.find_all('span', class_='common-item-icon')
                for reward_span in reward_spans:
                    reward_name = reward_span.get('title', '')
                    amount_span = reward_span.find('span', class_='common-item-icon__amount')
                    amount = amount_span.text.strip() if amount_span else "1"
                    preview_span = reward_span.find('span', class_='common-item-preview')
                    if preview_span:
                        style = preview_span.get('style', '')
                        url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        if url_match:
                            img_url = url_match.group(1)
                            if 'ticket' in img_url.lower() or 'SHOPTICKET' in img_url:
                                filename = download_ticket_image(img_url, reward_name, card_index)
                            else:
                                filename = None
                            all_rewards.append({
                                "name": reward_name,
                                "local_file": filename,
                                "url": img_url,
                                "amount": amount,
                                "type": "main"
                            })
            rewards_div = card.find('div', class_='mission-list-card__rewards')
            if rewards_div:
                icon_list = rewards_div.find('div', class_='icon-list')
                if icon_list:
                    sub_reward_spans = icon_list.find_all('span', class_='common-item-icon')
                    for sub_reward in sub_reward_spans:
                        sub_name = sub_reward.get('title', '')
                        preview = sub_reward.find('span', class_='common-item-preview')
                        if preview and sub_name:
                            style = preview.get('style', '')
                            url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                            if url_match:
                                sub_img_url = url_match.group(1)
                                amount_span = sub_reward.find('span', class_='common-item-icon__amount')
                                amount = amount_span.text.strip() if amount_span else "1"
                                if 'ticket' in sub_img_url.lower() or 'SHOPTICKET' in sub_img_url:
                                    sub_filename = download_ticket_image(sub_img_url, sub_name, card_index)
                                else:
                                    sub_filename = None
                                all_rewards.append({
                                    "name": sub_name,
                                    "local_file": sub_filename,
                                    "url": sub_img_url,
                                    "amount": amount,
                                    "type": "sub"
                                })
            progress_text = ""
            progress_bar = card.find('div', class_='progress-bar__text')
            if progress_bar:
                progress_text = progress_bar.text.strip()
            if mission_text:
                mission_item = {"description": mission_text}
                if all_rewards:
                    mission_item["rewards"] = all_rewards
                if progress_text:
                    mission_item["target"] = progress_text
                mission_list.append(mission_item)
        if mission_list:
            missions.append({"name": group_name, "period": date_text, "missions": mission_list})
    
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "target_type": target_type,
        "bonus_picks": bonus_picks,
        "rare_picks": rare_picks,
        "exclusive_flair": exclusive_flair,
        "missions": missions
    }
    
def extract_release_details(soup, url):
    """新セットリリースページの詳細情報を抽出（デッキ画像対応版）"""
    
    os.makedirs(TICKET_IMAGE_DIR, exist_ok=True)
    os.makedirs(DECK_IMAGE_DIR, exist_ok=True)
    
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    
    start_date = ""
    end_date = ""
    period_text = ""
    
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    
    # ゲームアップデート情報
    game_updates = []
    updates_section = soup.find('h2', string=re.compile(r'Game updates', re.IGNORECASE))
    if updates_section:
        ul = updates_section.find_next('ul')
        if ul:
            for li in ul.find_all('li'):
                game_updates.append(li.text.strip())
    
    # 今後のイベント情報
    upcoming_events = []
    events_section = soup.find('h2', string=re.compile(r'Paldean Wonders events', re.IGNORECASE))
    if not events_section:
        events_section = soup.find('h2', string=re.compile(r'Mega Shine events', re.IGNORECASE))
    if events_section:
        ul = events_section.find_next('ul')
        if ul:
            for li in ul.find_all('li'):
                link = li.find('a')
                if link:
                    event_name = link.text.strip()
                    event_url = link.get('href', '')
                    if event_url.startswith('/'):
                        event_url = 'https://www.pokemon-zone.com' + event_url
                    upcoming_events.append({
                        "name": event_name,
                        "url": event_url,
                        "description": li.text.strip()
                    })
                else:
                    upcoming_events.append({
                        "name": li.text.strip(),
                        "url": None,
                        "description": li.text.strip()
                    })
    
    # ショップアイテム
    shop_items = []
    shop_sections = soup.find_all('div', class_='shop-group-card')
    
    for section in shop_sections:
        section_title = section.find('h3')
        title_text = section_title.text.strip() if section_title else ""
        
        section_date = section.find('span', class_='banner-date__dates')
        date_text = section_date.text.strip() if section_date else ""
        
        items = []
        item_elements = section.find_all('div', class_='shop-group-card__item')
        
        for item in item_elements:
            name_elem = item.find('div', class_='shop-group-card__content-name')
            item_name = name_elem.text.strip() if name_elem else ""
            
            price_bar = item.find('div', class_='product-price-bar')
            price = ""
            currency_code = ""
            display_name = ""
            original_img_url = ""
            local_filename = None
            
            if price_bar:
                price_elem = price_bar.find('div', class_='product-price-bar__price')
                price = price_elem.text.strip() if price_elem else ""
                
                title_attr = price_bar.get('title', '') or price_bar.get('data-bs-original-title', '')
                if title_attr:
                    display_name = re.sub(r'^\d+x\s+', '', title_attr)
                    print(f"   📝 表示名: {display_name}")
                
                style = price_bar.get('style', '')
                if style:
                    url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                    if url_match:
                        original_img_url = url_match.group(1)
                        if original_img_url.startswith('//'):
                            original_img_url = 'https:' + original_img_url
                        
                        code_match = re.search(r'/([^/]+)\.webp', original_img_url)
                        if code_match:
                            currency_code = code_match.group(1)
                
                if original_img_url and display_name:
                    local_filename = download_ticket_image(original_img_url, display_name, 0)
                elif original_img_url and currency_code:
                    local_filename = download_ticket_image(original_img_url, currency_code, 0)
            
            if item_name and price:
                items.append({
                    "name": item_name,
                    "price": price,
                    "currency": currency_code,
                    "currency_image": local_filename
                })
        
        if items:
            shop_items.append({
                "title": title_text,
                "period": date_text,
                "items": items
            })
    
    # ポケ金セット情報
    gold_sets = []
    gold_sections = soup.find_all('div', class_='gold-shop-product-card')
    
    for gold in gold_sections:
        name_elem = gold.find('div', class_='gold-shop-product-card__name')
        gold_name = name_elem.text.strip() if name_elem else ""
        
        date_elem = gold.find('div', class_='gold-shop-product-card__date')
        gold_date = date_elem.text.strip() if date_elem else ""
        
        price_elem = gold.find('div', class_='product-price-bar__price')
        price = price_elem.text.strip() if price_elem else ""
        
        items = []
        item_elements = gold.find_all('div', class_='gold-shop-product-card__item')
        
        for item in item_elements:
            amount_elem = item.find('div', class_='gold-shop-product-card__item-amount')
            amount = amount_elem.text.strip() if amount_elem else ""
            
            bonus_elem = item.find('div', class_='gold-shop-product-card__item-bonus')
            is_bonus = bool(bonus_elem)
            
            if amount:
                items.append({
                    "amount": amount,
                    "is_bonus": is_bonus
                })
        
        if gold_name:
            gold_sets.append({
                "name": gold_name,
                "period": gold_date,
                "price": price,
                "items": items
            })
    
    # ソロバトル情報
    solo_battles = []
    battle_groups = soup.find_all('div', class_='solo-battle-group-card')
    
    for group in battle_groups:
        title_elem = group.find('div', class_='solo-battle-group-card__heading-title')
        battle_title = title_elem.text.strip() if title_elem else ""
        
        difficulty_elem = group.find('span', class_='solo-battle-group-card__difficulty')
        difficulty = difficulty_elem.text.strip() if difficulty_elem else ""
        
        battle_date = group.find('span', class_='banner-date__dates')
        date_text = battle_date.text.strip() if battle_date else ""
        
        tasks = []
        task_elements = group.find_all('div', class_='solo-battle-group-card__challenge')
        for task in task_elements:
            task_text = task.find('div', class_='solo-battle-group-card__challenge-text')
            if task_text:
                tasks.append(task_text.text.strip())
        
        if battle_title:
            solo_battles.append({
                "title": battle_title,
                "difficulty": difficulty,
                "period": date_text,
                "tasks": tasks
            })
    
    # ミッション情報（デッキ画像対応）
    missions = []
    mission_groups = soup.find_all('div', class_='mission-group')
    
    for group in mission_groups:
        group_name_elem = group.find('div', class_='mission-group__name')
        group_name = group_name_elem.text.strip() if group_name_elem else ""
        
        group_date = group.find('span', class_='banner-date__dates')
        date_text = group_date.text.strip() if group_date else ""
        
        mission_list = []
        mission_cards = group.find_all('div', class_='mission-list-card')
        
        for card in mission_cards:
            text_elem = card.find('div', class_='mission-list-card__text')
            mission_text = text_elem.text.strip() if text_elem else ""
            
            rewards = []
            preview_div = card.find('div', class_='mission-list-card__preview')
            if preview_div:
                reward_spans = preview_div.find_all('span', class_='common-item-icon')
                for reward in reward_spans:
                    reward_name = reward.get('title', '')
                    amount_span = reward.find('span', class_='common-item-icon__amount')
                    amount = amount_span.text.strip() if amount_span else "1"
                    
                    preview_span = reward.find('span', class_='common-item-preview')
                    if preview_span:
                        style = preview_span.get('style', '')
                        url_match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        if url_match:
                            img_url = url_match.group(1)
                            local_file = None
                            pokemon_type = None
                            
                            # deck-preview-icon のクラスから属性を取得
                            deck_icon = card.find('span', class_='deck-preview-icon')
                            if deck_icon:
                                classes = deck_icon.get('class', [])
                                for cls in classes:
                                    if '--type-' in cls:
                                        pokemon_type = cls.split('--type-')[1]
                                        print(f"   🃏 デッキタイプ: {pokemon_type}")
                            
                            # デッキ画像かチェック
                            if 'Deck' in reward_name or 'deck' in reward_name:
                                print(f"   🔍 デッキ報酬発見: {reward_name}")
                                card_img = None
                                
                                card_img = card.select_one('.game-card-image__img')
                                if not card_img:
                                    all_imgs = card.find_all('img')
                                    for img in all_imgs:
                                        src = img.get('src', '')
                                        if 'CardPreviews' in src or 'game-assets' in src:
                                            card_img = img
                                            break
                                if not card_img:
                                    if preview_div:
                                        card_img = preview_div.find('img')
                                
                                if card_img and card_img.get('src'):
                                    deck_img_url = card_img.get('src')
                                    if deck_img_url.startswith('/'):
                                        deck_img_url = 'https://www.pokemon-zone.com' + deck_img_url
                                    
                                    clean_name = re.sub(r'^\d+x\s+', '', reward_name)
                                    safe_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name)
                                    filename = f"{safe_name}.webp"
                                    filepath = os.path.join(DECK_IMAGE_DIR, filename)
                                    
                                    if not os.path.exists(filepath):
                                        try:
                                            resp = scraper.get(deck_img_url, timeout=15)
                                            if resp.status_code == 200:
                                                processed_image_data = process_emblem_image(resp.content)
                                                with open(filepath, 'wb') as f:
                                                    f.write(processed_image_data)
                                                print(f"   🃏 デッキ画像保存: {filename}")
                                                local_file = filename
                                        except Exception as e:
                                            print(f"   ⚠️ デッキ画像DLエラー: {e}")
                                    else:
                                        print(f"   ⏩ デッキ画像既存: {filename}")
                                        local_file = filename
                            
                            elif 'ticket' in img_url.lower() or 'SHOPTICKET' in img_url or 'EMBLEM' in img_url:
                                local_file = download_ticket_image(img_url, reward_name, 0)
                            
                            reward_data = {
                                "name": reward_name,
                                "local_file": local_file,
                                "url": img_url,
                                "amount": amount
                            }
                            if pokemon_type:
                                reward_data["type"] = pokemon_type
                            
                            rewards.append(reward_data)
            
            if mission_text:
                mission_item = {"description": mission_text}
                if rewards:
                    mission_item["rewards"] = rewards
                mission_list.append(mission_item)
        
        if mission_list:
            missions.append({
                "name": group_name,
                "period": date_text,
                "missions": mission_list
            })
    
    return {
        "url": url,
        "title": title,
        "period": {
            "text": period_text,
            "start_date": start_date,
            "end_date": end_date
        },
        "game_updates": game_updates,
        "upcoming_events": upcoming_events,
        "shop_items": shop_items,
        "gold_sets": gold_sets,
        "solo_battles": solo_battles,
        "missions": missions
    }
    
def extract_premium_shop_details(soup, url):
    title = ""
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.text.strip()
        print(f"📌 取得したタイトル: {title}")
    
    start_date = ""
    end_date = ""
    period_text = ""
    countdown = soup.find('span', class_='js-time-countdown-app')
    if countdown:
        start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
        end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
    dates_span = soup.find('span', class_='banner-date__dates')
    if dates_span:
        period_text = dates_span.text.strip()
    
    premium_card = None
    media_aside = soup.find('div', class_='media-block__aside')
    if media_aside:
        card_link = media_aside.find('a', href=True)
        if card_link and '/cards/' in card_link['href']:
            card_url = card_link.get('href', '')
            if card_url.startswith('/'):
                card_url = 'https://www.pokemon-zone.com' + card_url
            img = card_link.find('img')
            card_name = img.get('alt', '') if img else ""
            if card_name:
                simple_name = card_name.split(' - ')[0].split(' Art')[0].strip()
            card_div = card_link.find('div', {'data-pokemon-card-tooltip-app': True})
            card_id = card_div.get('data-pokemon-card-tooltip-app', '') if card_div else ""
            path_match = re.search(r'/cards/([^/]+/\d+)/[^/]+/$', card_url)
            card_path = path_match.group(1) if path_match else ""
            premium_card = {
                "name": simple_name if 'simple_name' in locals() else card_name,
                "full_name": card_name,
                "url": card_url,
                "id": card_id,
                "path": card_path
            }
            print(f"   💳 メイン目玉カード: {card_name}")
    
    premium_items = []
    shop_sections = soup.find_all('div', class_='shop-group-card')
    for section in shop_sections:
        section_title = section.find('h3')
        title_text = section_title.text.strip() if section_title else ""
        section_date = section.find('span', class_='banner-date__dates')
        date_text = section_date.text.strip() if section_date else ""
        items = []
        item_elements = section.find_all('div', class_='shop-group-card__item')
        for item in item_elements:
            name_elem = item.find('div', class_='shop-group-card__content-name')
            item_name = name_elem.text.strip() if name_elem else ""
            price_elem = item.find('div', class_='product-price-bar__price')
            price = price_elem.text.strip() if price_elem else ""
            currency_style = item.find('div', class_='product-price-bar')
            currency = ""
            if currency_style and currency_style.get('style'):
                match = re.search(r'url\([^)]*/([^/]+)\.webp', currency_style['style'])
                if match:
                    currency = match.group(1)
            tooltip = item.find('div', class_='shop-group-card__content')
            description = tooltip.get('title', '') if tooltip else ""
            if item_name and price:
                items.append({
                    "name": item_name,
                    "description": description,
                    "price": price,
                    "currency": currency
                })
        if items:
            premium_items.append({"title": title_text, "period": date_text, "items": items})
    
    missions = []
    mission_groups = soup.find_all('div', class_='mission-group')
    for group in mission_groups:
        group_name_elem = group.find('div', class_='mission-group__name')
        group_name = group_name_elem.text.strip() if group_name_elem else ""
        group_date = group.find('span', class_='banner-date__dates')
        date_text = group_date.text.strip() if group_date else ""
        mission_list = []
        mission_cards = group.find_all('div', class_='mission-list-card')
        for card in mission_cards:
            text_elem = card.find('div', class_='mission-list-card__text')
            if text_elem:
                parts = []
                for content in text_elem.contents:
                    if isinstance(content, str):
                        text = content.strip()
                        if text:
                            parts.append(text)
                    elif content.name == 'span' and 'rarity-icon' in content.get('class', []):
                        rarity_spans = content.find_all('span', class_='rarity-icon__icon')
                        diamond_count = len(rarity_spans)
                        if diamond_count == 1:
                            parts.append('♢')
                        elif diamond_count == 2:
                            parts.append('♢♢')
                        elif diamond_count == 3:
                            parts.append('♢♢♢')
                        elif diamond_count == 4:
                            parts.append('♢♢♢♢')
                        else:
                            parts.append('[レアリティ]')
                mission_text = ' '.join(parts)
            else:
                mission_text = ""
            rewards = []
            preview_div = card.find('div', class_='mission-list-card__preview')
            if preview_div:
                reward_spans = preview_div.find_all('span', class_='common-item-icon')
                for reward in reward_spans:
                    reward_name = reward.get('title', '')
                    amount_span = reward.find('span', class_='common-item-icon__amount')
                    amount = amount_span.text.strip() if amount_span else "1"
                    if reward_name:
                        rewards.append({"name": reward_name, "amount": amount, "type": "main"})
            rewards_div = card.find('div', class_='mission-list-card__rewards')
            if rewards_div:
                icon_list = rewards_div.find('div', class_='icon-list')
                if icon_list:
                    sub_reward_spans = icon_list.find_all('span', class_='common-item-icon')
                    for reward in sub_reward_spans:
                        reward_name = reward.get('title', '')
                        amount_span = reward.find('span', class_='common-item-icon__amount')
                        amount = amount_span.text.strip() if amount_span else "1"
                        if reward_name:
                            rewards.append({"name": reward_name, "amount": amount, "type": "sub"})
            progress_text = ""
            progress_bar = card.find('div', class_='progress-bar__text')
            if progress_bar:
                progress_text = progress_bar.text.strip()
            if mission_text:
                mission_list.append({
                    "description": mission_text,
                    "rewards": rewards,
                    "target": progress_text
                })
        if mission_list:
            missions.append({"name": group_name, "period": date_text, "missions": mission_list})
    
    description = ""
    article_body = soup.select_one('.article-detail__body')
    if article_body:
        first_p = article_body.find('p')
        if first_p:
            description = first_p.text.strip()
    
    return {
        "url": url,
        "title": title,
        "period": {"text": period_text, "start_date": start_date, "end_date": end_date},
        "premium_card": premium_card,
        "premium_items": premium_items,
        "missions": missions,
        "description": description
    }
    
def extract_event_details(soup, url, event_type):
    if event_type == "ranked_match":
        return extract_ranked_match_details(soup, url)
    elif event_type == "emblem_event":
        return extract_emblem_event_details(soup, url)
    elif event_type == "drop_event":
        return extract_drop_event_details(soup, url)
    elif event_type == "wonder_pick":
        return extract_wonder_pick_details(soup, url)
    elif event_type == "mass_outbreak":
        return extract_mass_outbreak_details(soup, url)
    elif event_type == "release":
        return extract_release_details(soup, url)
    elif event_type == "premium_shop":
        return extract_premium_shop_details(soup, url)
    else:
        title = ""
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.text.strip()
        start_date = ""
        end_date = ""
        period_text = ""
        countdown = soup.find('span', class_='js-time-countdown-app')
        if countdown:
            start_date = countdown.get('data-start', '').split('T')[0] if countdown.get('data-start') else ""
            end_date = countdown.get('data-end', '').split('T')[0] if countdown.get('data-end') else ""
        dates_span = soup.find('span', class_='banner-date__dates')
        if dates_span:
            period_text = dates_span.text.strip()
        return {
            "url": url,
            "title": title,
            "period": {"text": period_text, "start_date": start_date, "end_date": end_date}
        }

def save_event_data(event_data, event_type, base_output_dir):
    title = event_data['title']
    event_dir = os.path.join(base_output_dir, event_type)
    os.makedirs(event_dir, exist_ok=True)
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}.json"
    filepath = os.path.join(event_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(event_data, f, ensure_ascii=False, indent=2)
    print(f"💾 保存: {filepath}")
    return filepath

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"processed": [], "last_index": 0}

def save_progress(processed_urls, last_index):
    progress = {
        "processed": list(processed_urls),
        "last_index": last_index,
        "timestamp": datetime.now().isoformat()
    }
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def save_failed_url(url, error):
    failed = []
    if os.path.exists(FAILED_URLS_FILE):
        with open(FAILED_URLS_FILE, 'r', encoding='utf-8') as f:
            failed = json.load(f)
    failed.append({
        "url": url,
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    })
    with open(FAILED_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

def save_unprocessed_events(events, filename=UNPROCESSED_EVENTS_FILE):
    if not events:
        return
    try:
        existing_events = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        existing_urls = {e['url'] for e in existing_events}
        new_events = [e for e in events if e['url'] not in existing_urls]
        if new_events:
            all_events = existing_events + new_events
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, ensure_ascii=False, indent=2)
            print(f"📝 未処理イベント保存: {len(new_events)}件")
    except Exception as e:
        print(f"⚠️ 未処理イベント保存エラー: {e}")
        
def main():
    print("="*60)
    print("🎯 イベント詳細取得スクリプト")
    print(f"🖼️ 画像保存形式: {IMAGE_FORMAT} (品質: {IMAGE_QUALITY}%)")
    print("="*60)
    
    os.makedirs(TICKET_IMAGE_DIR, exist_ok=True)
    os.makedirs(DECK_IMAGE_DIR, exist_ok=True)
    
    try:
        from PIL import Image
        print("✅ Pillow 利用可能")
    except ImportError:
        print("❌ Pillowがインストールされていません")
        return
    
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("🧹 進捗ファイルをリセットしました")
    
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            all_events = json.load(f)
        print(f"📋 イベント数: {len(all_events)}件")
    except Exception as e:
        print(f"❌ JSON読み込みエラー: {e}")
        return
    
    ranked_events = []
    emblem_events = []
    drop_events = []
    wonder_events = []
    release_events = []
    premium_shop_events = []
    mass_outbreak_events = []
    other_events = []
    
    for event in all_events:
        title = event['title']
        event_type = get_event_type_from_title(title)
        if event_type == "ranked_match":
            ranked_events.append(event)
        elif event_type == "emblem_event":
            emblem_events.append(event)
        elif event_type == "drop_event":
            drop_events.append(event)
        elif event_type == "wonder_pick":
            wonder_events.append(event)
        elif event_type == "release":
            release_events.append(event)
        elif event_type == "premium_shop":
            premium_shop_events.append(event)
        elif event_type == "mass_outbreak":
            mass_outbreak_events.append(event)
        else:
            other_events.append(event)
    
    print(f"🎯 ランクマッチ: {len(ranked_events)}件")
    print(f"🎯 エンブレム: {len(emblem_events)}件")
    print(f"🎯 ドロップ: {len(drop_events)}件")
    print(f"🎯 ワンダーピック: {len(wonder_events)}件")
    print(f"🎯 リリース: {len(release_events)}件")
    print(f"🎯 プレミアムショップ: {len(premium_shop_events)}件")
    print(f"🎯 マスアウトブレイク: {len(mass_outbreak_events)}件")
    print(f"📌 その他: {len(other_events)}件")
    
    target_events = premium_shop_events + ranked_events + emblem_events + drop_events + wonder_events + release_events + mass_outbreak_events
    
    if other_events:
        save_unprocessed_events(other_events)
    
    if not target_events:
        print("❌ 処理対象のイベントが見つかりませんでした")
        return
    
    progress = load_progress()
    processed_urls = set(progress.get("processed", []))
    start_index = progress.get("last_index", 0)
    
    success_count = 0
    fail_count = 0
    
    for i, event in enumerate(target_events):
        if i < start_index:
            continue
        title = event['title']
        url = event['url']
        event_type = get_event_type_from_title(title)
        print(f"\n{'='*50}")
        print(f"📄 処理 {i+1}/{len(target_events)}: {title}")
        print(f"🏷️ タイプ: {event_type}")
        
        if url in processed_urls:
            print(f"⏩ 既に処理済み")
            continue
        
        resp = fetch_page(url)
        if resp:
            try:
                soup = BeautifulSoup(resp.content, 'html.parser')
                event_data = extract_event_details(soup, url, event_type)
                save_event_data(event_data, event_type, BASE_OUTPUT_DIR)
                processed_urls.add(url)
                success_count += 1
                save_progress(processed_urls, i)
            except Exception as e:
                print(f"❌ データ抽出エラー: {e}")
                import traceback
                traceback.print_exc()
                save_failed_url(url, str(e))
                fail_count += 1
        else:
            print(f"❌ ページ取得失敗")
            save_failed_url(url, "Failed to fetch page")
            fail_count += 1
        
        if i < len(target_events) - 1:
            wait_time = random.uniform(8, 15)
            print(f"⏳ {wait_time:.1f}秒待機...")
            time.sleep(wait_time)
    
    save_progress(processed_urls, len(target_events))
    print(f"\n{'='*60}")
    print(f"✅ 処理完了！成功: {success_count}件, 失敗: {fail_count}件")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 中断")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()