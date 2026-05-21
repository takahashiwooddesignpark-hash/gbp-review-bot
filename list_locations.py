"""
GOOGLE_PLACE_ID を調べるためのヘルパースクリプト。

使い方:
  python list_locations.py
"""

import os
import sys
from dotenv import load_dotenv
import gbp_client

load_dotenv()


def main() -> None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("ERROR: .env に GOOGLE_PLACES_API_KEY を設定してください")
        sys.exit(1)

    print("ウッドデザインパーク岡崎 を検索中...")
    try:
        result = gbp_client.find_place_id("ウッドデザインパーク岡崎", api_key)
        print(f"\n店舗名: {result.get('displayName', {}).get('text')}")
        print(f"住所: {result.get('formattedAddress')}")
        print(f"\n.env に以下を設定してください:")
        print(f"GOOGLE_PLACE_ID={result.get('id')}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
