from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def feed_item_kb(*, event_id: int, source_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Не интересно", callback_data=f"ni:{event_id}"),
                InlineKeyboardButton(text="Исключить источник", callback_data=f"xs:{source_id}"),
            ]
        ]
    )


def quick_interests_kb(options: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for o in options:
        rows.append([InlineKeyboardButton(text=f"+ {o}", callback_data=f"ai:{o}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def interests_manage_kb(interests: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in interests:
        rows.append([InlineKeyboardButton(text=f"− {i}", callback_data=f"ri:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

