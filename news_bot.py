# -*- coding: utf-8 -*-
"""
네이버 뉴스 키워드 모니터링 → 텔레그램 알림 봇 (여러 키워드 버전)
GitHub Actions에서 주기적으로 자동 실행됩니다.
"""
import os
import json
import requests

# ─────────────────────────────────────────────
# ★ 여기만 수정하세요! 모니터링할 키워드 목록
#   따옴표로 감싸고 쉼표로 구분합니다. 몇 개든 추가 가능.
# ─────────────────────────────────────────────
KEYWORDS = ["경상남도", "경남도청", "박완수"]

# GitHub Secrets에 등록한 값들을 자동으로 불러옵니다 (수정 불필요)
NAVER_ID = os.environ["NAVER_CLIENT_ID"]
NAVER_SECRET = os.environ["NAVER_CLIENT_SECRET"]
TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SEEN_FILE = "seen.json"  # 이미 보낸 기사 링크를 기억하는 파일


def load_seen():
    """이미 보낸 기사 링크 목록 불러오기"""
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_seen(seen):
    """보낸 기사 링크 목록 저장 (최근 1000개만 유지)"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen[-1000:], f, ensure_ascii=False, indent=1)


def fetch_news(keyword):
    """네이버 뉴스 검색 API로 해당 키워드의 최신 기사 20개 가져오기"""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET,
    }
    params = {"query": keyword, "display": 20, "sort": "date"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["items"]


def clean(text):
    """제목에 섞여 오는 HTML 태그/특수문자 제거"""
    for a, b in [("<b>", ""), ("</b>", ""), ("&quot;", '"'),
                 ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&apos;", "'")]:
        text = text.replace(a, b)
    return text


def send_telegram(msg):
    """텔레그램으로 메시지 보내기"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10,
    )


def main():
    seen = load_seen()
    total = 0

    for keyword in KEYWORDS:
        items = fetch_news(keyword)

        # 아직 안 보낸 기사만 골라내기
        new_items = [it for it in items if it["link"] not in seen]

        # 오래된 기사부터 순서대로 전송
        for it in reversed(new_items):
            title = clean(it["title"])
            msg = f"📰 [{keyword}] {title}\n{it['link']}"
            send_telegram(msg)
            seen.append(it["link"])
            total += 1

    save_seen(seen)
    print(f"새 기사 {total}건 전송 완료")


if __name__ == "__main__":
    main()
