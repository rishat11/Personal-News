from src.bot.handlers.callbacks import router as callbacks_router
from src.bot.handlers.commands import router as commands_router
from src.bot.handlers.free_text import router as free_text_router

__all__ = ["callbacks_router", "commands_router", "free_text_router"]
