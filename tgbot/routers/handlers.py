from io import BytesIO
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from ..keyboards.reply import main_menu
from ..services.openai_captioner import caption

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Пришли фото — я сгенерирую описание и ключевые слова для фотостоков.\n"
        "Команды: /help /lang_en /lang_ru /lang_both",
        reply_markup=main_menu()
    )

@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Как пользоваться:\n"
        "1) Пришлите фото.\n"
        "2) Я отвечу описанием (до 200 символов), ключевыми словами и хештегами.\n"
        "3) Команды: /lang_en или /lang_ru — выбрать язык; /lang_both — оба языка."
    )

# ---- выбор режима языка ----
@router.message(F.text.in_({"⚙️ Язык описания: EN"}))
@router.message(Command("lang_en"))
async def lang_en(message: Message, state: FSMContext):
    await state.update_data(lang="en", both=False)
    await message.answer("Язык описания: EN. Пришлите фото.")

@router.message(F.text.in_({"⚙️ Язык описания: RU"}))
@router.message(Command("lang_ru"))
async def lang_ru(message: Message, state: FSMContext):
    await state.update_data(lang="ru", both=False)
    await message.answer("Язык описания: RU. Пришлите фото.")

@router.message(F.text.in_({"🌐 Описание: RU+EN"}))
@router.message(Command("lang_both"))
async def lang_both(message: Message, state: FSMContext):
    # режим: генерируем на двух языках
    await state.update_data(both=True)  # lang игнорируем, т.к. будет оба
    await message.answer("Режим: RU+EN. Пришлите фото.")

# ---- обработка фото ----
@router.message(F.photo)
async def on_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    both = data.get("both", False)
    lang = data.get("lang", "en")

    # скачать bytes
    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    bio = BytesIO()
    await message.bot.download_file(file.file_path, bio)
    image_bytes = bio.getvalue()

    try:
        if both:
            # генерим отдельно RU и EN
            meta_ru = caption(image_bytes, lang="ru")
            meta_en = caption(image_bytes, lang="en")

            # формат RU
            desc_ru = meta_ru.get("description", "")
            title_ru = meta_ru.get("title", "")
            keywords_ru = ", ".join(meta_ru.get("keywords", []))
            hashtags_ru = " ".join([h if h.startswith('#') else f"#{h}" for h in meta_ru.get("hashtags", [])])

            # формат EN
            desc_en = meta_en.get("description", "")
            title_en = meta_en.get("title", "")
            keywords_en = ", ".join(meta_en.get("keywords", []))
            hashtags_en = " ".join([h if h.startswith('#') else f"#{h}" for h in meta_en.get("hashtags", [])])

            txt = (
                "<b>🇷🇺 Описание (RU)</b>\n"
                f"{desc_ru}\n"
                + (f"\n<b>Заголовок:</b> {title_ru}\n" if title_ru else "\n")
                + f"<b>Ключевые слова:</b> {keywords_ru}\n"
                f"<b>Хештеги:</b> {hashtags_ru}\n"
                "\n"
                "<b>🇬🇧 Description (EN)</b>\n"
                f"{desc_en}\n"
                + (f"\n<b>Title:</b> {title_en}\n" if title_en else "\n")
                + f"<b>Keywords:</b> {keywords_en}\n"
                f"<b>Hashtags:</b> {hashtags_en}"
            )
        else:
            # один язык (как раньше)
            meta = caption(image_bytes, lang=lang)
            desc = meta.get("description", "")
            title = meta.get("title", "")
            keywords = ", ".join(meta.get("keywords", []))
            hashtags = " ".join([h if h.startswith('#') else f"#{h}" for h in meta.get("hashtags", [])])

            txt = (f"<b>Описание</b>: {desc}\n\n"
                   + (f"<b>Заголовок:</b> {title}\n" if title else "")
                   + f"<b>Ключевые слова:</b> {keywords}\n"
                   f"<b>Хештеги:</b> {hashtags}")

    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")
        return

    await message.answer(txt)
