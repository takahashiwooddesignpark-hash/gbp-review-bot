import hashlib
import logging
import re
from typing import List, Dict, Any

log = logging.getLogger(__name__)

MAPS_URL = "https://www.google.com/maps/place/?q=place_id:{place_id}&hl=ja"


def scrape_reviews(place_id: str, max_reviews: int = 20) -> List[Dict[str, Any]]:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    url = MAPS_URL.format(place_id=place_id)
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(locale="ja-JP", timezone_id="Asia/Tokyo")
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            page.goto(url, timeout=30000)

        # Cookie同意ボタンを押す
        for btn_text in ["すべて同意する", "同意する", "Accept all"]:
            try:
                page.click(f'button:has-text("{btn_text}")', timeout=3000)
                page.wait_for_timeout(1000)
                break
            except Exception:
                pass

        # 口コミタブをクリック
        try:
            page.locator('button[aria-label*="口コミ"]').first.click(timeout=5000)
        except Exception:
            try:
                page.locator('[data-tab-index="1"]').click(timeout=5000)
            except Exception:
                pass

        page.wait_for_timeout(2000)

        # 最新順に並べ替え
        try:
            page.locator('[data-value="Sort"], [aria-label*="並べ替え"], [aria-label*="ソート"]').first.click(timeout=5000)
            page.wait_for_timeout(1000)
            page.locator('[data-index="1"]').first.click(timeout=3000)
            page.wait_for_timeout(2000)
        except Exception as e:
            log.warning("並べ替えボタンが見つかりませんでした: %s", e)

        # 口コミ要素を取得
        review_elements = page.locator('[data-review-id]').all()
        log.info("口コミ要素数: %d", len(review_elements))

        for elem in review_elements[:max_reviews]:
            try:
                # 投稿者名
                author_el = elem.locator('.d4r55').first
                author_name = author_el.inner_text(timeout=2000) if author_el.count() else "匿名"

                # 評価（星の数）
                rating = 0
                rating_el = elem.locator('[aria-label*="星"]').first
                if rating_el.count():
                    label = rating_el.get_attribute("aria-label") or ""
                    m = re.search(r"(\d)", label)
                    if m:
                        rating = int(m.group(1))

                # 投稿日時
                time_el = elem.locator('.rsqaWe').first
                time_text = time_el.inner_text(timeout=2000) if time_el.count() else ""

                # 「もっと見る」を展開
                try:
                    more = elem.locator('button:has-text("もっと見る")').first
                    if more.count():
                        more.click()
                        page.wait_for_timeout(500)
                except Exception:
                    pass

                # 本文
                text_el = elem.locator('.wiI7pd').first
                text = text_el.inner_text(timeout=2000) if text_el.count() else ""

                if author_name:
                    reviews.append({
                        "author_name": author_name,
                        "rating": rating,
                        "time": time_text,
                        "text": text,
                    })
            except Exception as e:
                log.debug("レビュー取得スキップ: %s", e)
                continue

        browser.close()

    return reviews


def review_id(review: Dict[str, Any]) -> str:
    key = f"{review.get('author_name', '')}_{review.get('text', '')[:100]}"
    return hashlib.md5(key.encode()).hexdigest()


def format_review(review: Dict[str, Any]) -> str:
    name = review.get("author_name", "匿名")
    rating = review.get("rating", 0)
    stars = "★" * rating + "☆" * (5 - rating)
    text = review.get("text", "（コメントなし）")
    time_text = review.get("time", "")

    return (
        f"【新しい口コミが届きました】\n"
        f"投稿者: {name}  {time_text}\n"
        f"評価: {stars}\n"
        f"コメント:\n{text}"
    )
