import os
import json
import html
import re
import requests

# ===== GitHub 금고에서 열쇠 꺼내기 =====
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
NAVER_CLIENT_ID = os.environ["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]

# ===== 검색할 키워드 (원하는 대로 수정하세요) =====
KEYWORDS = [
    "박완수",
    "경남도청",
    "경상남도",
]

SEEN_FILE = "seen.json"


def load_seen():
    """이미 보낸 기사 목록 불러오기"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_seen(links):
    """보낸 기사 목록 저장 (최근 2000개만 보관)"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(links[-2000:], f, ensure_ascii=False, indent=2)


def clean_title(raw):
    """제목에 섞인 코드 조각(<b> 등) 제거"""
    no_tags = re.sub(r"<[^>]+>", "", raw)
    return html.unescape(no_tags)


def search_naver_news(keyword):
    """네이버 뉴스 검색 (최신순 10개)"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": keyword,
        "display": 10,
        "sort": "date",
    }
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json().get("items", [])


def send_telegram(text):
    """텔레그램 채널로 메시지 보내기"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
    })


def main():
    seen = load_seen()
    for keyword in KEYWORDS:
        items = search_naver_news(keyword)
        for item in items:
            link = item.get("originallink") or item.get("link")
            if link in seen:
                continue
            title = clean_title(item["title"])
            send_telegram(f"📰 [{keyword}] {title}\n{link}")
            seen.append(link)
    save_seen(seen)


if __name__ == "__main__":
    main()
