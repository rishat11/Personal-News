from src.bot.keyboards.inline import feed_item_kb


def test_callback_formats() -> None:
    kb = feed_item_kb(event_id=123, source_id=7)
    buttons = kb.inline_keyboard[0]
    assert buttons[0].callback_data == "ni:123"
    assert buttons[1].callback_data == "xs:7"

