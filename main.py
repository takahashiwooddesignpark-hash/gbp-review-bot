"""
GBP口コミ監視Bot（Googleマップスクレイピング版）
新しい口コミを検知してLINE WORKSに通知する。

使い方:
  1回実行: python main.py
  定期実行: python main.py --loop
  cron推奨: */5 * * * * /path/to/venv/bin/python /path/to/main.py
"""

import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv

import scraper
import lineworks_client
import storage

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        log.error("環境変数 %s が設定されていません。.env を確認してください。", key)
        sys.exit(1)
    return val


def check_once() -> None:
    place_id = _require("GOOGLE_PLACE_ID")

    lw_client_id = _require("LW_CLIENT_ID")
    lw_client_secret = _require("LW_CLIENT_SECRET")
    lw_service_account = _require("LW_SERVICE_ACCOUNT")
    lw_private_key_path = _require("LW_PRIVATE_KEY_PATH")
    lw_bot_id = _require("LW_BOT_ID")
    lw_user_id = _require("LW_USER_ID")

    log.info("口コミを取得中: place_id=%s", place_id)
    reviews = scraper.scrape_reviews(place_id)
    log.info("取得件数: %d件", len(reviews))

    seen_ids = storage.load_seen_ids()

    # 初回実行時は既存口コミを既読にして通知しない
    if not seen_ids:
        log.info("初回実行: 既存の%d件を既読として登録します（通知しません）", len(reviews))
        seen_ids = {scraper.review_id(r) for r in reviews}
        storage.save_seen_ids(seen_ids)
        return

    new_reviews = [r for r in reviews if scraper.review_id(r) not in seen_ids]

    if not new_reviews:
        log.info("新しい口コミはありません")
        return

    log.info("新しい口コミ: %d件", len(new_reviews))

    for review in reversed(new_reviews):
        message = scraper.format_review(review)
        rid = scraper.review_id(review)
        log.info("通知送信: %s", review.get("author_name"))
        lineworks_client.send_message(
            text=message,
            bot_id=lw_bot_id,
            user_id=lw_user_id,
            client_id=lw_client_id,
            client_secret=lw_client_secret,
            service_account=lw_service_account,
            private_key_path=lw_private_key_path,
        )
        seen_ids.add(rid)

    storage.save_seen_ids(seen_ids)
    log.info("完了。通知送信済み: %d件", len(new_reviews))


def main() -> None:
    parser = argparse.ArgumentParser(description="GBP口コミ監視Bot")
    parser.add_argument("--loop", action="store_true", help="ポーリングモードで継続実行")
    args = parser.parse_args()

    if args.loop:
        interval = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
        log.info("ポーリングモード開始 (間隔: %d秒)", interval)
        while True:
            try:
                check_once()
            except Exception as e:
                log.error("エラーが発生しました: %s", e)
            time.sleep(interval)
    else:
        check_once()


if __name__ == "__main__":
    main()
