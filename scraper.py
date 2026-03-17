import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_landing_page(url: str) -> dict:
    """랜딩페이지 URL에서 상품 정보를 크롤링한다."""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # 불필요한 태그 제거
    for tag in soup.find_all(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
        tag.decompose()

    title = _extract_title(soup)
    price = _extract_price(soup)
    description = _extract_description(soup)
    images = _extract_images(soup, url)

    return {
        "url": url,
        "title": title,
        "price": price,
        "description": description,
        "image_count": len(images),
        "raw_text": _get_clean_text(soup),
    }


def _extract_title(soup: BeautifulSoup) -> str:
    """상품명 추출"""
    selectors = [
        "h1",
        ".product_name", ".prd_name", ".item_name",
        "[class*='product-name']", "[class*='product_title']",
        "meta[property='og:title']",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el.get("content", el.get_text(strip=True)) if el.name == "meta" else el.get_text(strip=True)

    og = soup.find("meta", property="og:title")
    if og:
        return og.get("content", "")

    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def _extract_price(soup: BeautifulSoup) -> str:
    """가격 추출"""
    selectors = [
        ".price", ".prd_price", ".product_price",
        "[class*='sale_price']", "[class*='sell_price']",
        "#span_product_price_text",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if text:
                return text
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """상세 설명 추출 (상세 영역 텍스트)"""
    selectors = [
        "#prdDetail", ".product_detail", ".prd_detail",
        "[class*='detail_cont']", "[class*='product-detail']",
        ".describe", "#detail",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 50:
                return text[:5000]

    # fallback: body의 주요 텍스트
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)[:5000]
    return ""


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """상품 이미지 URL 추출"""
    imgs = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(skip in src.lower() for skip in ["icon", "logo", "banner", "btn", "arrow"]):
            continue
        imgs.append(src)
    return imgs[:10]


def _get_clean_text(soup: BeautifulSoup) -> str:
    """페이지 전체의 클린 텍스트 (최대 8000자)"""
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:8000]
