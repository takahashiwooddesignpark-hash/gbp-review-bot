import requests
from typing import List, Dict, Any

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAIL_URL = "https://places.googleapis.com/v1/places/{place_id}"


def find_place_id(business_name: str, api_key: str) -> Dict[str, Any]:
    """ビジネス名からplace情報を取得する（初回セットアップ用）"""
    resp = requests.post(
        PLACES_SEARCH_URL,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress",
            "Content-Type": "application/json",
        },
        json={"textQuery": business_name, "languageCode": "ja"},
        timeout=30,
    )
    resp.raise_for_status()
    places = resp.json().get("places", [])
    if not places:
        raise ValueError(f"ビジネスが見つかりませんでした: {business_name}")
    # 最初の候補（ビジネス名が一致するものを優先）
    for place in places:
        if business_name in place.get("displayName", {}).get("text", ""):
            return place
    return places[0]


def fetch_reviews(place_id: str, api_key: str) -> List[Dict[str, Any]]:
    """Place IDからレビュー一覧を取得する（最新5件）"""
    url = PLACES_DETAIL_URL.format(place_id=place_id)
    resp = requests.get(
        url,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "reviews",
        },
        params={"languageCode": "ja"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("reviews", [])


def review_id(review: Dict[str, Any]) -> str:
    """レビューのユニークIDを生成する"""
    author = review.get("authorAttribution", {}).get("uri", "")
    publish_time = review.get("publishTime", "")
    return f"{author}_{publish_time}"


def format_review(review: Dict[str, Any]) -> str:
    name = review.get("authorAttribution", {}).get("displayName", "匿名")
    rating = review.get("rating", 0)
    stars = "★" * rating + "☆" * (5 - rating)
    text = review.get("text", {}).get("text", "（コメントなし）")
    relative_time = review.get("relativePublishTimeDescription", "")

    return (
        f"【新しい口コミが届きました】\n"
        f"投稿者: {name}  {relative_time}\n"
        f"評価: {stars}\n"
        f"コメント:\n{text}"
    )
