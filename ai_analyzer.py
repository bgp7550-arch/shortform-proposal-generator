import anthropic
from prompts import ANALYSIS_PROMPT, PROPOSAL_PROMPT


def create_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def analyze_product(client: anthropic.Anthropic, page_data: dict):
    """1차 분석: 제품/타겟/소구점 분석 (스트리밍)"""
    page_content = (
        f"상품명: {page_data['title']}\n"
        f"가격: {page_data['price']}\n"
        f"URL: {page_data['url']}\n\n"
        f"상세 내용:\n{page_data['description']}\n\n"
        f"페이지 전체 텍스트:\n{page_data['raw_text']}"
    )

    prompt = ANALYSIS_PROMPT.format(page_content=page_content)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def generate_proposal(client: anthropic.Anthropic, analysis: str, sender_name: str):
    """2차 분석: 영업 제안 이메일 생성 (스트리밍)"""
    prompt = PROPOSAL_PROMPT.format(
        analysis=analysis,
        sender_name=sender_name,
    )

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text
