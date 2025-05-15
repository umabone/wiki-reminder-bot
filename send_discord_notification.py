import requests
from bs4 import BeautifulSoup
import re
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def fetch_current_events():
    url = "https://bluearchive.wikiru.jp/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        raise Exception(f"ページの取得に失敗しました。ステータスコード: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # 「開催中のイベント」という文字を含む <p> タグを探す
    target_p = None
    for p in soup.find_all("p"):
        if "現在開催中のイベント" in p.get_text():
            target_p = p
            break

    if not target_p:
        raise Exception("開催中のイベントの見出し（pタグ）が見つかりませんでした。")

    # <p>の次に来る<ul>タグを取得！
    event_ul = target_p.find_next_sibling("ul")
    if not event_ul:
        raise Exception("イベント一覧のulタグが見つかりませんでした。")

    events = []
    for li in event_ul.find_all("li"):
        text = li.get_text(strip=True)
        match = re.match(r"(.*?)(\d{4}/\d{1,2}/\d{1,2}.*)", text)
        if match:
            name = match.group(1).strip()
            period = match.group(2).strip()
            events.append(f"{name}：{period}")
        else:
            # 日付がなくても一応追加してみる
            events.append(text)

    return events

def main():
    events = fetch_current_events()
    if not events:
        content = "現在、開催中のイベントはありません。"
    else:
        content = "📢 開催中のイベント情報：\n" + "\n".join(events)

    response = requests.post(WEBHOOK_URL, json={"content": content})
    if response.status_code != 204:
        raise Exception(f"通知に失敗しました。ステータスコード: {response.status_code}, レスポンス: {response.text}")

if __name__ == "__main__":
    main()
