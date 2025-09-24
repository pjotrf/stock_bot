import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from .config import BOT_TOKEN
from .routers import core_router
import logging


async def _main():
    bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(core_router)
    await dp.start_polling(bot)

def main():
    asyncio.run(_main())

if __name__ == "__main__":
    main()
