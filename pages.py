import streamlit as st
import json
from utils import RadarAnalyzer

st.set_page_config(page_title="RADAR News Analyzer", layout="wide")
st.title("📰 RADAR - Выявление горячих финансовых новостей")


with st.form("event_form"):
    headline = st.text_input(
        "📝 Заголовок события (headline)",
        "",
        help="Краткий заголовок события"
    )

    why_now = st.text_area(
        "📌 Почему важно сейчас (why_now)",
        "",
        help="1–2 фразы о новизне, подтверждениях и масштабе затронутых активов"
    )

    entities = st.text_input(
        "🏷 Сущности (entities)",
        "",
        help="Компании, тикеры, страны или сектора, связанные с событием (через запятую)"
    )

    sources = st.text_area(
        "🔗 Источники (sources)",
        "",
        help="3–5 проверяемых ссылок: оригинал, подтверждение, апдейт (по строкам)"
    )

    timeline = st.text_area(
        "⏱ Таймлайн события (timeline)",
        "",
        help="Ключевые метки времени: первое сообщение → подтверждение → уточнение"
    )

    dedup_group = st.text_input(
        "🆔 ID кластера дубликатов (dedup_group)",
        "",
        help="Идентификатор кластера дубликатов/перепечаток"
    )

    submit = st.form_submit_button("✅ Сгенерировать черновик")


if submit:
    # Формируем словарь события
    sample_event = {
        "headline": headline,
        "why_now": why_now,
        "entities": [e.strip() for e in entities.split(",") if e.strip()],
        "sources": [s.strip() for s in sources.splitlines() if s.strip()],
        "timeline": [t.strip() for t in timeline.splitlines() if t.strip()],
        "dedup_group": dedup_group
    }

    analyzer = RadarAnalyzer()

    with st.spinner("Получаем факты и источники..."):
        try:
            facts = analyzer.fetch_event_sources(headline)
            st.subheader("🔗 Факты и источники")
            st.text(facts)
        except Exception as e:
            st.error(f"Ошибка при получении фактов: {e}")



    with st.spinner("Генерируем черновик поста..."):
        try:
            draft = analyzer.generate_draft(sample_event)
            st.subheader("📝 Черновик поста")
            st.json(draft)
        except Exception as e:
            st.error(f"Ошибка при генерации черновика: {e}")


    with st.spinner("Оцениваем горячесть события..."):
        try:
            hotness = analyzer.evaluate_hotness(sample_event)
            sample_event["hotness"] = hotness
            st.metric("🔥 Горячесть новости", hotness)
        except Exception as e:
            st.error(f"Ошибка при оценке горячести: {e}")

    # -------------------------------
    # 4️⃣ Отображаем итоговое событие
    # -------------------------------
    st.subheader("📌 Исходное событие (с горячестью)")
    st.json(sample_event)
