import requests
from bs4 import BeautifulSoup
import re
import os
import logging
from datetime import datetime, timedelta

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数から取得
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# 環境変数がなければ、ここにURLを直接指定することもできる
if not WEBHOOK_URL:
    # DiscordのWebhook URLを設定してね！
    WEBHOOK_URL = "https://discord.com/api/webhooks/あなたのWebhook URL"

def extract_original_time(date_str):
    """元の文字列から時間部分 (HH:MM) を抽出する"""
    time_match = re.search(r"(\d{1,2}):(\d{2})", date_str)
    if time_match:
        return f"{time_match.group(1)}:{time_match.group(2)}"
    return None

def format_event_date(start_date, end_date, original_date_text):
    """元の日付テキストから時間を抽出し、指定された形式でフォーマットする"""
    logger.info(f"元の日付テキスト: {original_date_text}")
    
    # 日付部分の分割
    if "～" in original_date_text:
        date_parts = original_date_text.split("～")
    elif "~" in original_date_text:
        date_parts = original_date_text.split("~")
    else:
        # 分割できない場合はデフォルトのフォーマット使用
        start_str = start_date.strftime('%Y/%m/%d %H:%M')
        end_str = end_date.strftime('%Y/%m/%d %H:%M')
        logger.warning(f"日付テキストを分割できませんでした: {original_date_text}")
        return f"{start_str} ~ {end_str}"
    
    # 開始日時部分と終了日時部分
    start_date_str = date_parts[0].strip()
    end_date_str = date_parts[1].strip() if len(date_parts) > 1 else ""
    
    logger.info(f"開始日部分: {start_date_str}")
    logger.info(f"終了日部分: {end_date_str}")
    
    # 開始日のフォーマット (年/月/日)
    start_formatted = start_date.strftime('%Y/%m/%d')
    
    # 終了日のフォーマット (年/月/日) - 開始日の年を使用
    end_formatted = f"{start_date.year}/{end_date.strftime('%m/%d')}"
    
    # 元の時間形式を抽出
    start_time = extract_original_time(start_date_str) or start_date.strftime('%H:%M')
    end_time = extract_original_time(end_date_str) or end_date.strftime('%H:%M')
    
    logger.info(f"抽出した開始時間: {start_time}")
    logger.info(f"抽出した終了時間: {end_time}")
    
    # 出力形式: 2025/05/14 11:00 ~ 2025/05/21 10:59
    formatted_result = f"{start_formatted} {start_time} ~ {end_formatted} {end_time}"
    logger.info(f"フォーマット結果: {formatted_result}")
    return formatted_result

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
        
        # デバッグ用：HTMLを保存
        with open("debug_html.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("デバッグ用にHTMLを保存しました。")
        
        # イベント情報を格納するリスト
        current_events = []  # 現在開催中のイベントを格納するリスト
        
        # 現在の日付を取得
        today = datetime.now()
        logger.info(f"現在の日付: {today.strftime('%Y/%m/%d')}")
        
        # 日付パターンの正規表現（より厳密に）
        date_patterns = [
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}.*?\d{1,2}:\d{2}.*?[～~].*?\d{1,2}[/-]\d{1,2}.*?\d{1,2}:\d{2}",  # 2025/5/14 11:00 ～ 5/21 3:59
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}.*?[～~].*?\d{1,2}[/-]\d{1,2}",  # 2025/5/14 ～ 5/21
            r"\d{4}[/-]\d{1,2}[/-]\d{1,2}.*?[～~].*?",  # 2025/5/14 ～ （終了日不明）
            r"[～~].*?\d{4}[/-]\d{1,2}[/-]\d{1,2}",  # ～ 2025/5/21（開始日不明）
            r"\(\d{4}[/-]\d{1,2}[/-]\d{1,2}.*?\d{1,2}:\d{2}.*?[～~].*?\d{1,2}[/-]\d{1,2}.*?\d{1,2}:\d{2}\)"  # (2025/5/14 11:00 ～ 5/21 3:59)
        ]
        
        # 時間のパターン - これを使って余計な時間表記を除去する
        time_pattern = r'\(\s*\d{1,2}:\d{2}\)'
        
        # リスト項目（li）のみに絞って探す
        logger.info("リスト項目(li)を探します...")
        list_items = soup.find_all("li")
        logger.info(f"{len(list_items)}個のリスト項目が見つかりました。")
        
        for li in list_items:
            text = li.get_text(strip=True)
            
            # 短すぎるテキストは除外
            if len(text) < 10:
                continue
                
            logger.info(f"リスト項目のテキスト: {text}")
            
            # 日付パターンを含むかチェック
            date_found = False
            date_text = ""
            
            # 括弧付きの日付パターンを優先して検索
            if "(" in text and ")" in text:
                # 括弧内のテキストを抽出
                bracket_matches = re.findall(r'\((.*?)\)', text)
                for bracket_text in bracket_matches:
                    if "～" in bracket_text or "~" in bracket_text:
                        for pattern in date_patterns:
                            match = re.search(pattern, "(" + bracket_text + ")")
                            if match:
                                date_found = True
                                date_text = bracket_text
                                logger.info(f"括弧内の日付パターン発見: {date_text}")
                                break
                    if date_found:
                        break
                        
            # 括弧で見つからなかった場合は通常パターンで検索
            if not date_found:
                for pattern in date_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        date_found = True
                        date_text = match.group(0)
                        # 括弧がある場合は除去
                        date_text = date_text.strip("()")
                        logger.info(f"日付パターン発見: {date_text}")
                        break
                    if date_found:
                        break
            
            # 日付パターンが見つからなかったらスキップ
            if not date_found:
                continue
                
            # 日付をパースして現在進行中かチェック
            try:
                # 開始日と終了日を抽出
                if "～" in date_text:
                    date_parts = date_text.split("～")
                elif "~" in date_text:
                    date_parts = date_text.split("~")
                else:
                    continue  # 分割できない場合はスキップ
                
                # 開始日の処理
                start_date_str = date_parts[0].strip()
                start_match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", start_date_str)
                if not start_match:
                    continue  # 開始日が見つからない場合はスキップ
                
                start_year = int(start_match.group(1))
                start_month = int(start_match.group(2))
                start_day = int(start_match.group(3))
                
                # 時間の処理
                start_hour = 0
                start_minute = 0
                time_match = re.search(r"(\d{1,2}):(\d{2})", start_date_str)
                if time_match:
                    start_hour = int(time_match.group(1))
                    start_minute = int(time_match.group(2))
                
                start_date = datetime(start_year, start_month, start_day, start_hour, start_minute)
                
                # 終了日の処理
                if len(date_parts) > 1:
                    end_date_str = date_parts[1].strip()
                    
                    # 終了日に年が含まれていない場合は開始日の年を使用
                    end_match = re.search(r"(?:(\d{4})[/-])?(\d{1,2})[/-](\d{1,2})", end_date_str)
                    if not end_match:
                        # 終了日が見つからない場合は1ヶ月後に設定
                        end_date = start_date + timedelta(days=30)
                    else:
                        end_year = int(end_match.group(1)) if end_match.group(1) else start_year
                        end_month = int(end_match.group(2))
                        end_day = int(end_match.group(3))
                        
                        # 時間が含まれている場合は考慮
                        end_hour = 23  # デフォルトは23:59
                        end_minute = 59
                        
                        # 元の日付文字列から終了時間を抽出
                        if end_date_str:
                            end_time_match = re.search(r"(\d{1,2}):(\d{2})", end_date_str)
                            if end_time_match:
                                end_hour = int(end_time_match.group(1))
                                end_minute = int(end_time_match.group(2))
                        
                        end_date = datetime(end_year, end_month, end_day, end_hour, end_minute)
                else:
                    # 終了日が指定されていない場合は1ヶ月後に設定
                    end_date = start_date + timedelta(days=30)
                
                # 現在日が開始日と終了日の間かチェック
                if start_date <= today <= end_date:
                    logger.info(f"現在開催中のイベント発見: {text}")
                    
                    # ----- イベント名抽出処理改善 -----
                    
                    # 1. まず日付パターンをテキストから除去
                    event_name = text
                    for pattern in date_patterns:
                        event_name = re.sub(pattern, "", event_name)
                    
                    # 2. 時間表記 (10:59) や (3:59) などを除去
                    event_name = re.sub(time_pattern, "", event_name)
                    
                    # 3. 空の括弧 () を削除
                    event_name = re.sub(r'\(\s*\)', "", event_name)
                    
                    # 4. 余分な記号や空白を整理
                    event_name = re.sub(r'[\s　]+', ' ', event_name).strip()
                    event_name = re.sub(r'[:：]$', '', event_name).strip()
                    
                    # 5. 最後にチェック - あまりにも短すぎる場合や空になった場合
                    if len(event_name) < 5:
                        # オリジナルテキストから時間表記だけ除去して使用
                        event_name = re.sub(r'\(\s*\d{1,2}:\d{2}\)', "", text).strip()
                        # 空の括弧も除去
                        event_name = re.sub(r'\(\s*\)', "", event_name)
                    
                    # イベント名が空になってしまった場合は「不明なイベント」とする
                    if not event_name:
                        event_name = "不明なイベント"
                    
                    # 日付情報の整形 - 元の日付テキストを渡して時間情報を保持
                    formatted_date = format_event_date(start_date, end_date, date_text)
                    
                    # イベント情報のフォーマット (イベント名 (日付))
                    formatted_event = f"{event_name} ({formatted_date})"
                    
                    if formatted_event not in current_events:  # 重複チェック
                        current_events.append(formatted_event)
            
            except Exception as e:
                logger.warning(f"日付解析中にエラーが発生: {e} - テキスト: {date_text}")
                continue
        
        # 何も見つからなかった場合のフォールバック処理
        if not current_events:
            logger.warning("リスト項目から現在開催中のイベントが見つかりませんでした。別の方法で再試行します。")
            
            # ulタグの中を直接探してみる
            for ul in soup.find_all("ul"):
                text = ul.get_text(strip=True)
                if len(text) > 20:  # 十分な長さがあるか
                    for pattern in date_patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            date_text = match.group(0)
                            logger.info(f"ul内で日付パターン発見: {date_text}")
                            
                            try:
                                # 開始日と終了日の処理（上と同じロジック）
                                if "～" in date_text or "~" in date_text:
                                    date_parts = date_text.split("～") if "～" in date_text else date_text.split("~")
                                    
                                    # 開始日の処理
                                    start_date_str = date_parts[0].strip()
                                    start_match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", start_date_str)
                                    if start_match:
                                        start_year = int(start_match.group(1))
                                        start_month = int(start_match.group(2))
                                        start_day = int(start_match.group(3))
                                        
                                        # 時間の処理
                                        start_hour = 0
                                        start_minute = 0
                                        time_match = re.search(r"(\d{1,2}):(\d{2})", start_date_str)
                                        if time_match:
                                            start_hour = int(time_match.group(1))
                                            start_minute = int(time_match.group(2))
                                        
                                        start_date = datetime(start_year, start_month, start_day, start_hour, start_minute)
                                        
                                        # 終了日の処理
                                        if len(date_parts) > 1:
                                            end_date_str = date_parts[1].strip()
                                            end_match = re.search(r"(?:(\d{4})[/-])?(\d{1,2})[/-](\d{1,2})", end_date_str)
                                            if end_match:
                                                end_year = int(end_match.group(1)) if end_match.group(1) else start_year
                                                end_month = int(end_match.group(2))
                                                end_day = int(end_match.group(3))
                                                
                                # 時間が含まれている場合は考慮
                                                end_hour = 23  # デフォルトは23:59
                                                end_minute = 59
                                                
                                                # 終了日の時間を元のテキストから抽出
                                                if end_date_str:
                                                    end_time_match = re.search(r"(\d{1,2}):(\d{2})", end_date_str)
                                                    if end_time_match:
                                                        end_hour = int(end_time_match.group(1))
                                                        end_minute = int(end_time_match.group(2))
                                                        logger.info(f"終了時間を抽出: {end_hour}:{end_minute}")
                                                
                                                end_date = datetime(end_year, end_month, end_day, end_hour, end_minute)
                                                
                                                # 現在日が範囲内かチェック
                                                if start_date <= today <= end_date:
                                                    # イベント名を抽出する処理も改善
                                                    event_text = ul.get_text(strip=True)
                                                    # 日付パターンと時間表記を除去
                                                    event_text = re.sub(pattern, "", event_text)
                                                    event_text = re.sub(time_pattern, "", event_text)
                                                    # 空の括弧を削除
                                                    event_text = re.sub(r'\(\s*\)', "", event_text)
                                                    
                                                    event_text = re.sub(r'[\s　]+', ' ', event_text).strip()
                                                    
                                                    if len(event_text) < 5:
                                                        event_text = "イベント情報"
                                                        
                                                    formatted_date = format_event_date(start_date, end_date, date_text)
                                                    formatted_event = f"{event_text} ({formatted_date})"
                                                    
                                                    if formatted_event not in current_events:
                                                        current_events.append(formatted_event)
                            except Exception as e:
                                logger.warning(f"フォールバック処理中にエラー: {e}")
                                continue
        
        logger.info(f"最終的に取得した現在開催中のイベント数: {len(current_events)}")
        return current_events
        
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
            content = "📢 開催中のイベント情報: \n" + "\n".join(events)
            logger.info(f"Webhookに{len(events)}件のイベント情報を送信します。")

        if not WEBHOOK_URL:
            logger.error("WEBHOOK_URLが設定されていません。")
            raise Exception("WEBHOOK_URLが環境変数に設定されていないか、コードで直接指定されていません。")
            
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