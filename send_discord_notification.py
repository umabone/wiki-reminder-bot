import requests
import datetime
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"お知らせ！\nWikiチェック内容\n({now})"
    response = requests.post(WEBHOOK_URL, json={"content": content})
    if response.status_code != 204:
        raise Exception(f"通知失敗！Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    main()
