import requests
from bs4 import BeautifulSoup
import re
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def fetch_current_events():
    url = "https://bluearchive.wikiru.jp/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        logger.info(f"URLにリクエスト送信中: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            logger.error(f"ページの取得に失敗しました。ステータスコード: {response.status_code}")
            raise Exception(f"ページの取得に失敗しました。ステータスコード: {response.status_code}")
        
        logger.info("ページの取得に成功しました。HTMLの解析を開始します。")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 「開催中のイベント」という文字を含む要素を探す - タグを限定しない
        target_element = None
        
        # h2, h3, h4, p, div などのタグをチェック
        for tag in ["h2", "h3", "h4", "p", "div"]:
            for element in soup.find_all(tag):
                if "開催中のイベント" in element.get_text():
                    target_element = element
                    logger.info(f"「開催中のイベント」を含む{tag}タグを発見しました。")
                    break
            if target_element:
                break
        
        if not target_element:
            # 代替方法：クラス名を使用して特定のセクションを探す
            for div in soup.find_all("div", class_=["side-box", "event-box", "contents-box"]):
                if "開催中" in div.get_text() and "イベント" in div.get_text():
                    target_element = div
                    logger.info("クラス名から「開催中のイベント」セクションを発見しました。")
                    break
                    
        if not target_element:
            logger.error("開催中のイベントの見出しが見つかりませんでした。")
            raise Exception("開催中のイベントの見出しが見つかりませんでした。")
        
        # ULタグを探す - 複数の方法で探索
        event_ul = None
        
        # 方法1: 直近の兄弟要素を確認
        event_ul = target_element.find_next_sibling("ul")
        
        # 方法2: 親要素内のULを探す
        if not event_ul:
            parent = target_element.parent
            event_ul = parent.find("ul")
            if event_ul:
                logger.info("親要素内からULタグを発見しました。")
        
        # 方法3: 近くの要素を探す
        if not event_ul:
            # targetの後にある最初のUL要素を探す
            next_tags = target_element.find_all_next()
            for tag in next_tags[:10]:  # 最初の10個の要素だけ確認
                if tag.name == "ul":
                    event_ul = tag
                    logger.info("近くの要素からULタグを発見しました。")
                    break
        
        if not event_ul:
            logger.error("イベント一覧のulタグが見つかりませんでした。")
            raise Exception("イベント一覧のulタグが見つかりませんでした。")
        
        events = []
        for li in event_ul.find_all("li"):
            text = li.get_text(strip=True)
            logger.info(f"リストアイテム発見: {text}")
            
            # 正規表現を調整してより多くのフォーマットに対応
            match = re.search(r"(.*?)[\(（]?(\d{4}[/-]\d{1,2}[/-]\d{1,2}.*?)[\)）]?$", text)
            if not match:
                match = re.search(r"(.*?)(\d{4}[/-]\d{1,2}[/-]\d{1,2}.*)", text)
            
            if match:
                name = match.group(1).strip()
                period = match.group(2).strip()
                events.append(f"{name}：{period}")
            else:
                # 日付がなくても一応追加
                events.append(text)
        
        logger.info(f"取得したイベント数: {len(events)}")
        return events
        
    except requests.RequestException as e:
        logger.error(f"リクエスト中にエラーが発生しました: {e}")
        raise
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        raise

def main():
    try:
        events = fetch_current_events()
        if not events:
            content = "現在、開催中のイベントはありません。"
            logger.info("開催中のイベントはありません。")
        else:
            content = "📢 開催中のイベント情報：\n" + "\n".join(events)
            logger.info(f"Webhookに{len(events)}件のイベント情報を送信します。")

        if not WEBHOOK_URL:
            logger.error("WEBHOOK_URLが設定されていません。")
            raise Exception("WEBHOOK_URLが環境変数に設定されていません。")
            
        response = requests.post(WEBHOOK_URL, json={"content": content})
        if response.status_code != 204:
            logger.error(f"通知に失敗しました。ステータスコード: {response.status_code}, レスポンス: {response.text}")
            raise Exception(f"通知に失敗しました。ステータスコード: {response.status_code}, レスポンス: {response.text}")
        else:
            logger.info("Webhookへの通知に成功しました。")
            
    except Exception as e:
        logger.error(f"メイン処理中にエラーが発生しました: {e}")
        # 実運用では、ここでエラー通知を送信するか、リトライロジックを実装するとよい

if __name__ == "__main__":
    main()