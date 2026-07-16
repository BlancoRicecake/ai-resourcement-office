from __future__ import annotations

import json

import httpx

from .base import LLMProvider
from ..config import Settings


class OpenAILLMProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def extract_constraints(self, text: str) -> dict | None:
        if not self.settings.openai_enabled:
            return None
        prompt = (
            "한국어 해외여행 요청에서 사용자가 말한 조건만 JSON 객체로 추출하라. "
            "날짜·비용 계산은 하지 말고, 불명확한 값은 생략하라. 각 항목은 "
            "{value, hardness, reason} 형식이며 hardness는 hard 또는 soft다. "
            "허용 키: destination_country,destination_city,destination_code,travel_month,departure_date,"
            "return_date,nights,trip_days,adults,children,rooms,budget_krw,pace,direct_required,max_stops,"
            "checked_baggage,bed_count,required_amenities,ground_mode,rental_class,sports_model_preferred,"
            "driver_age,parking_required,special_meals_per_day,special_meal_budget_krw,avoid_crowds,"
            "must_visit_places,dietary_needs,mobility_needs. JSON 외 문자를 출력하지 마라.\n"
            f"요청: {text}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": self.settings.openai_model, "input": prompt, "max_output_tokens": 800},
            )
            response.raise_for_status()
        data = response.json()
        output = data.get("output_text", "")
        if not output:
            output = "".join(
                content.get("text", "")
                for item in data.get("output", [])
                for content in item.get("content", [])
                if content.get("type") == "output_text"
            )
        cleaned = output.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except (TypeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    async def summarize(self, normalized_payload: dict) -> str | None:
        if not self.settings.openai_enabled:
            return None
        prompt = (
            "다음은 코드가 계산한 한국인 해외여행 비교 결과다. 사실과 숫자를 추가하지 말고, "
            "추천 이유와 가장 중요한 확인 사항을 한국어 4문장 이내로 설명하라. "
            "연결된 공급자의 현재 결과일 뿐 전 세계 최저가가 아님을 밝혀라.\n"
            f"{normalized_payload}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": self.settings.openai_model, "input": prompt, "max_output_tokens": 350},
            )
            response.raise_for_status()
        data = response.json()
        if data.get("output_text"):
            return data["output_text"]
        chunks = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    chunks.append(content.get("text", ""))
        return "\n".join(filter(None, chunks)) or None
