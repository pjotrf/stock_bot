from aiogram import Router
from .handlers import router as handlers_router

core_router = Router()
core_router.include_router(handlers_router)
