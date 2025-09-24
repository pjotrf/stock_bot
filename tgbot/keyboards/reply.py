from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 Загрузить фото")],
            [
                KeyboardButton(text="⚙️ Язык описания: EN"),
                KeyboardButton(text="⚙️ Язык описания: RU"),
            ],
            [KeyboardButton(text="🌐 Описание: RU+EN")],  # новая кнопка
        ],
        resize_keyboard=True
    )
