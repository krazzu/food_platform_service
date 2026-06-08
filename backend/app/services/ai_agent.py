"""
LangChain agent that interprets natural language supplier queries,
calls search tools, and returns a ranked recommendation with explanation.
"""
import logging
from typing import Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models.supplier import Supplier
from . import search_service
from .llm_providers import get_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — умный ассистент для поиска поставщиков продуктов питания в России.
Твоя задача: помочь пользователю найти подходящих поставщиков, используя доступные инструменты поиска.

Порядок работы:
1. Проанализируй запрос пользователя: выдели категорию товара, регион, бюджет, требования к сертификатам.
2. Вызови инструменты поиска с нужными параметрами.
3. Изучи результаты и выбери 3–5 лучших поставщиков.
4. Напиши краткую рекомендацию на русском языке: почему каждый поставщик подходит, на что обратить внимание.

Отвечай только на русском языке. Будь конкретным и практичным."""


def make_agent(db: AsyncSession):
    """Build a LangChain agent with DB-session-scoped tools."""

    @tool
    async def search_suppliers(
        query: str,
        category: Optional[str] = None,
        region: Optional[str] = None,
        max_min_order: Optional[float] = None,
        has_certificates: Optional[bool] = None,
    ) -> str:
        """
        Поиск поставщиков по запросу. Возвращает список подходящих поставщиков с контактами.
        Параметры:
          query: текстовый запрос (например "органическая мука")
          category: категория товара (например "Бакалея")
          region: регион или город (например "Москва")
          max_min_order: максимальный допустимый минимальный заказ в рублях
          has_certificates: True если требуются сертификаты
        """
        results = await search_service.merged_search(
            db=db,
            query=query,
            category=category,
            region=region,
            max_min_order=max_min_order,
            has_certificates=has_certificates,
            limit=10,
        )
        if not results:
            return "Поставщики не найдены."

        lines = []
        for r in results:
            s = r.supplier
            lines.append(
                f"[ID={s.id}] {s.name} | "
                f"Категория: {s.category.name if s.category else '—'} | "
                f"Регион: {s.region or s.city or '—'} | "
                f"Мин. заказ: {s.min_order_amount} {s.min_order_unit or ''} | "
                f"Телефон: {s.phone or '—'} | "
                f"Email: {s.email or '—'} | "
                f"Сайт: {s.website or '—'} | "
                f"Сертификаты: {', '.join(s.certificate_types or []) or 'нет'} | "
                f"Цены: {s.price_range_description or '—'} | "
                f"Доставка: {s.delivery_conditions or '—'}"
            )
        return "\n".join(lines)

    @tool
    async def get_supplier_details(supplier_id: int) -> str:
        """Получить полную информацию о конкретном поставщике по его ID."""
        result = await db.execute(
            select(Supplier)
            .options(selectinload(Supplier.category))
            .where(Supplier.id == supplier_id)
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return f"Поставщик с ID={supplier_id} не найден."

        s = supplier
        return (
            f"Название: {s.name}\n"
            f"Описание: {s.description}\n"
            f"Категория: {s.category.name if s.category else '—'}\n"
            f"Город: {s.city}, Регион: {s.region}\n"
            f"Телефон: {s.phone}\n"
            f"Email: {s.email}\n"
            f"Сайт: {s.website}\n"
            f"Мин. заказ: {s.min_order_amount} {s.min_order_unit or ''}\n"
            f"Цены: {s.price_range_description}\n"
            f"Сертификаты: {', '.join(s.certificate_types or []) or 'нет'}\n"
            f"Условия доставки: {s.delivery_conditions}\n"
            f"Регионы доставки: {', '.join(s.delivery_regions or []) or '—'}\n"
            f"Заметки: {s.notes or '—'}"
        )

    llm = get_provider().get_llm()
    tools = [search_suppliers, get_supplier_details]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)


async def run_ai_search(query: str, db: AsyncSession) -> str:
    """Run the LangChain agent and return its final text response."""
    provider = get_provider()
    if not provider.is_available():
        return (
            f"AI-рекомендации недоступны: провайдер '{settings.llm_provider}' "
            "не настроен (проверьте API-ключ в .env)."
        )

    try:
        executor = make_agent(db)
        result = await executor.ainvoke({"input": query})
        return result.get("output", "")
    except Exception as exc:
        logger.error("AI agent error: %s", exc)
        return f"Ошибка AI-агента: {exc}"
