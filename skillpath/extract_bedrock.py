"""Bedrock extractor. The model reads sentences flexibly; verify.py decides what is kept.

Calls are opt-in (USE_BEDROCK=true) and cached by posting text + model + prompt version,
so a rerun of the same data costs nothing and gives the same claims.
"""
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .models import Claim
from .sections import SECTION_LABELS

PROMPT_VERSION = 'extract-v1'
SYSTEM = """당신은 채용공고의 기술 요구사항을 추출합니다.
- 자격요건과 우대사항에서 기술(언어, 프레임워크, 데이터베이스, 클라우드, 도구)만 추출합니다.
- evidence에는 공고 원문의 한 줄을 글자 그대로 복사합니다. 요약하거나 고쳐 쓰지 않습니다.
- requirement는 원문 기준입니다. 자격요건 안에 있어도 '우대'라고 쓴 문장은 preferred입니다.
- 학력, 경력 연수, 성향 같은 비기술 조건은 제외합니다.
- 원문에 없는 기술을 추측해서 넣지 않습니다."""


class SkillItem(BaseModel):
    skill: str = Field(description='기술명 (예: Python, AWS, Kubernetes)')
    evidence: str = Field(description='공고 원문에서 그대로 복사한 한 줄')
    section: Literal['qualifications', 'preferred']
    requirement: Literal['required', 'preferred']


class Extraction(BaseModel):
    items: list[SkillItem]


def render(posting):
    parts = [f"직무: {posting.get('role', '')}", f"제목: {posting.get('title', '')}"]
    for section, label in SECTION_LABELS.items():
        parts.append(f"[{section}] {label}\n{posting['sections'].get(section) or '(없음)'}")
    return '\n\n'.join(parts)


class BedrockExtractor:
    def __init__(self, model, region, cache_dir, client=None):
        if client is None:
            from anthropic import AnthropicBedrockMantle
            client = AnthropicBedrockMantle(aws_region=region)
        self.client, self.model = client, model
        self.cache_dir = Path(cache_dir)
        self.usage = {'calls': 0, 'cache_hits': 0, 'input_tokens': 0, 'output_tokens': 0}

    def _key(self, text):
        return hashlib.sha256(f'{self.model}\n{PROMPT_VERSION}\n{text}'.encode()).hexdigest()[:24]

    def extract(self, posting, skills=None):
        text = render(posting)
        path = self.cache_dir / f'{self._key(text)}.json'
        if path.exists():
            self.usage['cache_hits'] += 1
            items = json.loads(path.read_text(encoding='utf-8'))['items']
        else:
            items = self._call(text)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'posting_id': posting['id'], 'model': self.model,
                                        'prompt_version': PROMPT_VERSION, 'items': items},
                                       ensure_ascii=False, indent=2), encoding='utf-8')
        return [Claim(posting['id'], i['section'], i['skill'], i['evidence'], i['requirement'], 'bedrock')
                for i in items]

    def _call(self, text):
        response = self.client.messages.parse(
            model=self.model, max_tokens=16000, system=SYSTEM,
            messages=[{'role': 'user', 'content': text}], output_format=Extraction)
        self.usage['calls'] += 1
        self.usage['input_tokens'] += response.usage.input_tokens
        self.usage['output_tokens'] += response.usage.output_tokens
        if response.stop_reason != 'end_turn' or response.parsed_output is None:
            # A refused or truncated answer is a failed extraction, never an empty one.
            raise RuntimeError(f'extraction stopped: {response.stop_reason}')
        return [item.model_dump() for item in response.parsed_output.items]
