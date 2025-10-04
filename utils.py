from datetime import datetime
import json
import math
import os
import requests
from dotenv import load_dotenv

load_dotenv()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
API_KEY = os.getenv("VSE_GPT_API_KEY")

class RadarAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("VSE_GPT_API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY не найден! Установите VSE_GPT_API_KEY в окружении.")
        self.url = "https://api.vsegpt.ru/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer sk-or-vv-1a8dfaf4540f762b6c3297bda76e35360f21132ede51920cebc10796f1d6ccab",
            "Content-Type": "application/json"
        }
        self.event = None
        self.sources_and_facts = None
        self.draft = None

    # -------------------------------
    # Получение источников и фактов
    # -------------------------------
    def fetch_event_sources(self, headline: str) -> str:
        json_data = {
            "model": "perplexity/latest-large-online",
            "messages": [
                {"role": "system", "content": "Ты аналитическая система RADAR. Найди официальные источники и факты по событию."},
                {"role": "user", "content": f"Найди ссылки, точное название датасета и статистику пользователей для события: {headline}"}
            ]
        }
        response = requests.post(self.url, headers=self.headers, json=json_data)
        response.raise_for_status()
        self.sources_and_facts = response.json()["choices"][0]["message"]["content"]
        return self.sources_and_facts

    # -------------------------------
    # Генерация черновика поста
    # -------------------------------
    def generate_draft(self, event_json: dict) -> dict:

        combined_event = {
            **event_json,
            "facts": self.sources_and_facts
        }
        self.event = combined_event

        event_str = json.dumps(combined_event, ensure_ascii=False)
        json_data = {
            "model": "openai/gpt-4.1",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты редактор деловых новостей. Используй ТОЛЬКО предоставленные факты "
                        "и события. Формат ответа — JSON с ключами headline, lead, bullets, citation."
                    )
                },
                {
                    "role": "user",
                    "content": f"Сделай черновик поста для события и фактов:\n{event_str}"
                }
            ]
        }

        response = requests.post(self.url, headers=self.headers, json=json_data)
        response.raise_for_status()
        draft_str = response.json()["choices"][0]["message"]["content"]

        try:
            self.draft = json.loads(draft_str)
        except json.JSONDecodeError:
            self.draft = {"error": "Не удалось распарсить JSON", "raw": draft_str}
        return self.draft

    def evaluate_hotness(self, event_json: dict) -> float:
        """
        Примерная оценка горячести новости (0.0 - 1.0)
        Берёт сущности прямо из формы (entities), без предопределённых категорий.
        """
        score = 0.0


        num_sources = len(event_json.get("sources", []))
        if num_sources > 0:
            score += min(0.2 * math.log1p(num_sources), 0.3)

        entities = event_json.get("entities", [])
        num_entities = len(entities)
        if num_entities > 0:
            score += min(0.1 * num_entities, 0.3)

        now = datetime.now()
        dates = []
        for d in event_json.get("timeline", []):
            try:
                date_str = d.split(" — ")[0].strip()
                dates.append(datetime.strptime(date_str, "%d %B %Y"))
            except Exception:
                continue

        if dates:
            most_recent = max(dates)
            days_diff = (now - most_recent).days
            score += max(0, 0.3 - (days_diff * 0.02))  # чем свежее, тем выше


        if self.sources_and_facts and len(self.sources_and_facts) > 200:
            score += 0.1

        return round(min(score, 1.0), 2)


# -------------------------------
if __name__ == "__main__":
    headline = "Центробанк впервые оценил потенциальный вклад НДС в инфляцию"

    analyzer = RadarAnalyzer()


    analyzer.fetch_event_sources(headline)

    sample_event = {
        "headline": headline,
        "hotness": 0.88,
        "why_now": "Центробанк впервые оценил потенциальный вклад НДС в инфляцию",
        "entities": ["Центробанк"],
        "sources": ["https://www.rbc.ru"],
        "timeline": [
            "30 октября 2025 — пресс-релиз о публикации",
            "30 октября 2025 — анонс на официальном сайте"
        ],
        "dedup_group": "cb_tax_inflation_20251030"
    }


    analyzer.generate_draft(sample_event)


    analyzer.display()
