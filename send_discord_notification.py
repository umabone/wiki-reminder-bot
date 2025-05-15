import requests
from bs4 import BeautifulSoup
import re
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def fetch_current_events():
    url = "https://bluearchive.wikiru.jp/"
    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        raise Exception(f"ページの取得に失敗しました。ステータスコード: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    event_section = soup.find(string=re.compile("開催中のイベント"))
    if not event_section:
        raise Exception("開催中のイベントセクションが見つかりませんでした。")

    parent = event_section.find_parent()
    if not parent:
        raise Exception("開催中のイベントセクションの親要素が見つかりませんでした。")

    events = []
    for li in parent.find_next_siblings("ul"):
        for item in li.find_all("li"):
            text = item.get_text(strip=True)
            match = re.match(r"(.*?)(\d{4}/\d{1,2}/\d{1,2}.*)", text)
            if match:
                name = match.group(1).strip()
                period = match.group(2).strip()
                events.append(f"{name}：{period}")
        break

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
