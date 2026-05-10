import os
import json
import time
import random
import re
from bs4 import BeautifulSoup
import cloudscraper
import requests

# -------- カード取得スクリプトから流用した回避テクニック -------- #

# ランダムUser-Agentの候補リスト（拡充版）
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4; rv:118.0) Gecko/20100101 Firefox/118.0",
]

# Cloudscraperの設定
try:
    import cloudscraper
    use_cloudscraper = True
    scraper = cloudscraper.create_scraper(
        delay=15,
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True,
        },
        interpreter='js2py'
    )
    print("✅ cloudscraperを初期化しました")
except ImportError:
    import requests
    use_cloudscraper = False
    print("⚠️ cloudscraperが使えないのでrequestsで代用します。")

def enhanced_request(url, retry_count=5):
    """強化版リクエスト関数"""
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                wait_time = 30 * (2 ** (attempt - 1))
                print(f"🔄 リトライ {attempt+1}/{retry_count}: {wait_time}秒待機...")
                time.sleep(wait_time)
            
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Referer": "https://www.google.com/",
            }
            
            print(f"🌐 リクエスト送信: {url}")
            
            if use_cloudscraper and scraper:
                resp = scraper.get(url, headers=headers, timeout=45)
            else:
                session = requests.Session()
                resp = session.get(url, headers=headers, timeout=45)
            
            if resp.status_code == 200:
                # Cloudflareチャレンジページかどうかチェック
                if "Just a moment" in resp.text or "Checking your browser" in resp.text:
                    print("⚠️ Cloudflareチャレンジページを検出")
                    if attempt < retry_count - 1:
                        continue
                    else:
                        return None
                
                print(f"✅ ステータスコード: {resp.status_code}")
                return resp
            
            elif resp.status_code == 403:
                print(f"⚠️ 403 Forbidden (試行 {attempt+1}/{retry_count})")
                if attempt < retry_count - 1:
                    continue
                else:
                    return None
            else:
                print(f"⚠️ 予期しないステータスコード: {resp.status_code}")
                if attempt < retry_count - 1:
                    continue
                else:
                    return None
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            if attempt < retry_count - 1:
                continue
            else:
                return None
    
    return None

def is_valid_events_page(soup):
    """有効なイベント一覧ページかどうかをチェック"""
    articles = soup.find_all('article', class_='featured-article-preview')
    if len(articles) > 0:
        return True
    
    if "Do not sell or share my personal information" in soup.text:
        print("⚠️ プライバシー設定ページを検出しました")
        return False
    
    return False

def extract_events_from_page(soup, base_url):
    """ページからイベント情報を抽出"""
    events = []
    articles = soup.find_all('article', class_='featured-article-preview')
    
    for article in articles:
        title_tag = article.find('h2', class_='featured-article-preview__title')
        if title_tag and title_tag.find('a'):
            link_tag = title_tag.find('a')
            title = link_tag.get_text(strip=True)
            relative_url = link_tag.get('href')
            
            if relative_url.startswith('/'):
                full_url = base_url + relative_url
            else:
                full_url = relative_url
            
            events.append({
                "title": title,
                "url": full_url
            })
    
    return events

def get_next_page_url(soup, base_url, current_url):
    """
    正しい「次のページ」のURLを取得
    - 「Next」と書かれたリンクを優先
    - 数字のページネーションから現在のページ+1を探す
    - 「»」は最後のページへのリンクなので無視
    """
    
    # 方法1: 「Next」というテキストのリンクを探す
    next_links = soup.find_all('a', string=re.compile(r'Next', re.IGNORECASE))
    for link in next_links:
        # 親要素がpagination__control--nextかチェック
        parent = link.find_parent('div', class_='pagination__control--next')
        if parent:
            href = link.get('href')
            if href:
                print(f"🔍 'Next'リンクを発見: {href}")
                return convert_to_absolute_url(href, base_url, current_url)
    
    # 方法2: ページネーションの数字から次のページを特定
    pagination = soup.find('div', class_='pagination__pages')
    if pagination:
        # 現在のページ番号を取得
        current_span = pagination.find('span', class_='pagination__link--is-active')
        if current_span and current_span.text.strip().isdigit():
            current_page = int(current_span.text.strip())
            
            # 次のページ番号のリンクを探す
            for link in pagination.find_all('a', class_='pagination__link'):
                if link.text.strip().isdigit():
                    page_num = int(link.text.strip())
                    if page_num == current_page + 1:
                        href = link.get('href')
                        if href:
                            print(f"🔍 ページ番号から次のページを発見: {page_num} -> {href}")
                            return convert_to_absolute_url(href, base_url, current_url)
    
    # 方法3: 「»」は最後のページなので無視（ここには来ないはず）
    return None

def convert_to_absolute_url(href, base_url, current_url):
    """相対URLを絶対URLに変換"""
    if href.startswith('/'):
        return base_url + href
    elif href.startswith('?'):
        base_page_url = current_url.split('?')[0]
        return base_page_url + href
    else:
        return href

def smart_delay(consecutive_success=0, consecutive_fails=0):
    """成功率に基づいて待機時間を決定"""
    base_delay = 15
    
    if consecutive_fails > 0:
        base_delay = 30 * (2 ** min(consecutive_fails, 3))
        print(f"⚠️ 連続{consecutive_fails}回失敗のため待機時間延長: {base_delay}秒")
    elif consecutive_success > 2:
        base_delay = max(15, base_delay - (consecutive_success - 2) * 3)
    
    final_delay = base_delay * random.uniform(0.75, 1.25)
    print(f"⏳ 待機時間: {final_delay:.1f}秒")
    time.sleep(final_delay)
    
    return final_delay

def save_progress(events, failed_urls, page_num, filename="progress.json"):
    """進捗を保存"""
    progress = {
        "events": events,
        "failed_urls": failed_urls,
        "last_page": page_num,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    print(f"💾 進捗を保存しました (ページ {page_num})")

def load_progress(filename="progress.json"):
    """保存した進捗を読み込み"""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def extract_all_events_with_bypass():
    """メイン処理：ブロック回避機能付きで全イベントを収集"""
    output_dir = '/storage/emulated/0/html/pkpk'
    output_path = os.path.join(output_dir, 'イベントurl_all.json')
    progress_path = os.path.join(output_dir, 'progress.json')
    base_url = 'https://www.pokemon-zone.com'
    
    os.makedirs(output_dir, exist_ok=True)
    
    progress = load_progress(progress_path)
    if progress:
        print("📂 保存済みの進捗を読み込みました")
        all_events = progress.get("events", [])
        failed_urls = progress.get("failed_urls", [])
        start_page = progress.get("last_page", 1)
        print(f"   - 取得済みイベント: {len(all_events)}件")
        print(f"   - 失敗URL: {len(failed_urls)}件")
        print(f"   - 最終ページ: {start_page}")
    else:
        all_events = []
        failed_urls = []
        start_page = 1
    
    current_url = f'https://www.pokemon-zone.com/events/?page={start_page}'
    page_num = start_page
    consecutive_success = 0
    consecutive_fails = 0
    max_pages = 50
    
    print(f"\n🚀 イベント収集を開始 (開始ページ: {page_num})")
    print("="*60)
    
    while current_url and page_num <= max_pages:
        print(f"\n📄 ページ {page_num} を処理中...")
        print(f"URL: {current_url}")
        
        if page_num > start_page:
            smart_delay(consecutive_success, consecutive_fails)
        
        resp = enhanced_request(current_url, retry_count=5)
        
        if resp and resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            if not is_valid_events_page(soup):
                print("⚠️ 有効なイベントページではありません")
                consecutive_fails += 1
                consecutive_success = 0
                
                page_num += 1
                current_url = f'https://www.pokemon-zone.com/events/?page={page_num}'
                continue
            
            page_events = extract_events_from_page(soup, base_url)
            
            if page_events:
                existing_urls = {e["url"] for e in all_events}
                new_events = [e for e in page_events if e["url"] not in existing_urls]
                
                all_events.extend(new_events)
                print(f"✅ {len(page_events)}件のイベントを発見 (新規: {len(new_events)}件)")
                print(f"📊 合計: {len(all_events)}件")
                
                consecutive_success += 1
                consecutive_fails = 0
            else:
                print("⚠️ イベントが見つかりませんでした")
                consecutive_fails += 1
                consecutive_success = 0
            
            # 次のページURLを取得（改良版）
            next_url = get_next_page_url(soup, base_url, current_url)
            
            if next_url:
                print(f"➡️ 次のページ: {next_url}")
                current_url = next_url
                
                # URLからページ番号を抽出
                match = re.search(r'page=(\d+)', current_url)
                if match:
                    page_num = int(match.group(1))
                else:
                    page_num += 1
                
                if page_num % 5 == 0:
                    save_progress(all_events, failed_urls, page_num, progress_path)
            else:
                print("🏁 最終ページに到達しました")
                current_url = None
        
        else:
            print(f"❌ ページ {page_num} の取得に失敗")
            failed_urls.append(current_url)
            consecutive_fails += 1
            consecutive_success = 0
            
            save_progress(all_events, failed_urls, page_num, progress_path)
            
            if consecutive_fails >= 3:
                print("⚠️ 連続3回失敗しました。一時停止します...")
                time.sleep(300)
                
                if consecutive_fails >= 5:
                    print("❌ 連続5回失敗。処理を中断します。")
                    break
            
            page_num += 1
            current_url = f'https://www.pokemon-zone.com/events/?page={page_num}'
    
    # 最終保存
    print("\n" + "="*60)
    print("📦 最終データを保存中...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    
    if failed_urls:
        failed_path = os.path.join(output_dir, '失敗したurl.json')
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_urls, f, ensure_ascii=False, indent=2)
        print(f"❌ 失敗URL: {len(failed_urls)}件")
    
    print(f"\n{'='*60}")
    print(f"🎉 収集完了！")
    print(f"📊 総イベント数: {len(all_events)}件")
    print(f"💾 保存先: {output_path}")
    
    if all_events:
        print("\n📋 取得したイベント（最初の5件）:")
        for i, event in enumerate(all_events[:5]):
            print(f"  {i+1}. {event['title']}")
            print(f"     {event['url']}")
    
    print(f"{'='*60}\n")
    
    return all_events

if __name__ == "__main__":
    try:
        extract_all_events_with_bypass()
    except KeyboardInterrupt:
        print("\n\n⏹️ ユーザーによる中断を検出")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()