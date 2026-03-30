from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from database import db
from keyboards import (
    get_main_menu_keyboard,
    get_catalog_keyboard,
    get_category_keyboard,
    get_product_keyboard,
    get_profile_keyboard,
    get_payment_methods_keyboard,
    get_payment_ready_keyboard,
    get_send_to_admin_keyboard,
    get_back_to_shop_keyboard
)
from config import ADMIN_IDS

catalog_router = Router()


class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()


class UserOrderStates(StatesGroup):
    waiting_for_email = State()
    confirming_email = State()
    waiting_for_code = State()


@catalog_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    is_admin = user.id in ADMIN_IDS
    
    # Регистрируем пользователя
    db.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    await message.answer(
        "👋 Добро пожаловать в магазин Brawl Stars!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )


@catalog_router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Обработчик команды /catalog"""
    categories = db.get_all_categories()
    is_admin = message.from_user.id in ADMIN_IDS
    
    if not categories:
        text = "📦 Каталог пуст. Категории пока не добавлены."
        if is_admin:
            text += "\n\nИспользуйте /admin для добавления категорий и товаров."
            from keyboards import get_admin_keyboard
            await message.answer(text, reply_markup=get_admin_keyboard())
        else:
            await message.answer(text, reply_markup=get_main_menu_keyboard(is_admin=is_admin))
        return
    
    await message.answer(
        "📦 Каталог товаров:\n\n"
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard(categories, is_admin=is_admin)
    )


@catalog_router.callback_query(F.data == "show_catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать каталог с категориями"""
    categories = db.get_all_categories()
    is_admin = callback.from_user.id in ADMIN_IDS
    
    if not categories:
        text = "📦 Каталог пуст. Категории пока не добавлены."
        if is_admin:
            text += "\n\nИспользуйте /admin для добавления категорий и товаров."
            from keyboards import get_admin_keyboard
            await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
        else:
            await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard(is_admin=is_admin))
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📦 Каталог товаров:\n\n"
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard(categories, is_admin=is_admin)
    )
    await callback.answer()


@catalog_router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Вернуться к каталогу"""
    categories = db.get_all_categories()
    is_admin = callback.from_user.id in ADMIN_IDS
    
    if not categories:
        text = "📦 Каталог пуст. Категории пока не добавлены."
        if is_admin:
            text += "\n\nИспользуйте /admin для добавления категорий и товаров."
            from keyboards import get_admin_keyboard
            await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
        else:
            await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard(is_admin=is_admin))
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📦 Каталог товаров:\n\n"
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard(categories, is_admin=is_admin)
    )
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery, bot: Bot):
    """Показать товары категории"""
    category_id = int(callback.data.split("_")[1])
    category = db.get_category(category_id)
    
    if not category:
        await callback.answer("Категория не найдена!", show_alert=True)
        return
    
    products = db.get_products_by_category(category_id)
    keyboard = get_category_keyboard(category_id, products)
    
    if not products:
        text = f"📁 Категория: {category['name']}\n\n"
        if category.get('description'):
            text += f"{category.get('description', '')}\n\n"
        text += "Товары в этой категории пока не добавлены."
    else:
        text = f"📁 Категория: {category['name']}\n\n"
        if category.get('description'):
            text += f"{category['description']}\n\n"
        text += "Выберите товар:"
    
    # Если сообщение содержит фото, нужно удалить его и отправить новое текстовое
    try:
        if callback.message.photo:
            await callback.message.delete()
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
    except Exception as e:
        # Если не удалось обновить, отправляем новое сообщение
        try:
            await callback.message.delete()
        except:
            pass
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=keyboard
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, bot: Bot):
    """Показать информацию о товаре"""
    product_id = int(callback.data.split("_")[1])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    category = db.get_category(product['category_id'])
    
    text = f"🛍️ {product['name']}\n\n"
    
    if product.get('description'):
        text += f"📝 {product['description']}\n\n"
    
    text += f"💰 Цена: {product['price']}₽\n"
    text += f"📁 Категория: {category['name']}"
    
    keyboard = get_product_keyboard(product_id, product['category_id'])
    
    # Если есть фото, отправляем его с подписью
    if product.get('photo_file_id'):
        try:
            # Пытаемся обновить сообщение с фото
            if callback.message.photo:
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=product['photo_file_id'],
                        caption=text
                    ),
                    reply_markup=keyboard
                )
            else:
                # Если сообщение без фото, удаляем старое и отправляем новое с фото
                await callback.message.delete()
                sent_message = await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=product['photo_file_id'],
                    caption=text,
                    reply_markup=keyboard
                )
        except Exception:
            # Если не удалось отправить фото, отправляем текст
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard
                )
            except Exception:
                # Если и это не удалось, отправляем новое сообщение
                await callback.message.delete()
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=text,
                    reply_markup=keyboard
                )
    else:
        # Если фото нет, просто обновляем текст
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery, bot: Bot):
    """Обработчик покупки товара - показываем способы оплаты"""
    product_id = int(callback.data.split("_")[1])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    
    # Регистрируем пользователя если его еще нет
    user = callback.from_user
    db.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    text = f"💳 Выберите способ оплаты для товара:\n\n"
    text += f"🛍️ {product['name']}\n"
    text += f"💰 Цена: {product['price']}₽"
    
    from keyboards import get_payment_methods_keyboard
    
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=get_payment_methods_keyboard(product_id)
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=get_payment_methods_keyboard(product_id)
            )
    except Exception:
        # Если не удалось обновить, отправляем новое сообщение
        try:
            await callback.message.delete()
        except:
            pass
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=get_payment_methods_keyboard(product_id)
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("payment_qr_"))
async def show_qr_payment(callback: CallbackQuery, bot: Bot):
    """Показать QR код для оплаты"""
    product_id = int(callback.data.split("_")[2])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    
    # Создаем заказ
    db.create_order(
        user_id=user_id,
        product_id=product_id,
        product_name=product['name'],
        price=product['price']
    )
    
    # Путь к QR коду
    import os
    qr_path = os.path.join("data", "qr_code.png")
    
    text = f"📱 Оплата через СБП (QR код)\n\n"
    text += f"🛍️ Товар: {product['name']}\n"
    text += f"💰 Сумма: {product['price']}₽\n\n"
    text += "Отсканируйте QR код для оплаты.\n"
    text += "После оплаты прикрепите скришот платежа."
    
    keyboard = get_payment_ready_keyboard(product_id, product['category_id'])
    
    # Проверяем наличие QR кода
    if os.path.exists(qr_path):
        try:
            # Отправляем фото с QR кодом
            from aiogram.types import FSInputFile
            photo_file = FSInputFile(qr_path)
            
            if callback.message.photo:
                try:
                    await callback.message.delete()
                except:
                    pass
            
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo_file,
                caption=text,
                reply_markup=keyboard
            )
        except Exception as e:
            # Если не удалось отправить фото, отправляем текст
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=text + "\n\n⚠️ QR код временно недоступен.",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        text + "\n\n⚠️ QR код временно недоступен.",
                        reply_markup=keyboard
                    )
            except:
                try:
                    await callback.message.delete()
                except:
                    pass
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=text + "\n\n⚠️ QR код временно недоступен.",
                    reply_markup=keyboard
                )
    else:
        # Если QR код не найден, отправляем сообщение
        text += "\n\n⚠️ QR код не найден. Пожалуйста, загрузите файл qr_code.png в папку data."
        try:
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(text, reply_markup=keyboard)
        except:
            try:
                await callback.message.delete()
            except:
                pass
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=text,
                reply_markup=keyboard
            )
    
    await callback.answer("Заказ оформлен! Отсканируйте QR код для оплаты.")


@catalog_router.callback_query(F.data.startswith("payment_card_"))
async def show_card_payment(callback: CallbackQuery, bot: Bot):
    """Показать реквизиты банковской карты"""
    product_id = int(callback.data.split("_")[2])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    
    # Создаем заказ
    db.create_order(
        user_id=user_id,
        product_id=product_id,
        product_name=product['name'],
        price=product['price']
    )
    
    text = f"💳 Оплата банковской картой\n\n"
    text += f"🛍️ Товар: {product['name']}\n"
    text += f"💰 Сумма: {product['price']}₽\n\n"
    text += "Реквизиты для оплаты:\n"
    text += "Номер карты: []\n"
    text += "Получатель: []\n\n"
    text += "После оплаты прикрепите скришот платежа."
    
    keyboard = get_payment_ready_keyboard(product_id, product['category_id'])
    
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
    except Exception:
        try:
            await callback.message.delete()
        except:
            pass
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=text,
            reply_markup=keyboard
        )
    
    await callback.answer("Заказ оформлен! Используйте указанные реквизиты для оплаты.")


@catalog_router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль пользователя"""
    user_id = callback.from_user.id
    
    # Регистрируем пользователя если его еще нет
    user = callback.from_user
    db.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Получаем информацию о пользователе
    user_info = db.get_user(user_id)
    purchases_count = db.get_user_purchases_count(user_id)
    
    if not user_info:
        await callback.answer("Ошибка загрузки профиля!", show_alert=True)
        return
    
    # Формируем текст профиля
    text = "👤 Профиль\n\n"
    
    if user_info.get('first_name'):
        text += f"Имя: {user_info['first_name']}"
        if user_info.get('last_name'):
            text += f" {user_info['last_name']}"
        text += "\n"
    
    if user_info.get('username'):
        text += f"Username: @{user_info['username']}\n"
    
    # Форматируем дату регистрации
    try:
        # SQLite возвращает дату в формате 'YYYY-MM-DD HH:MM:SS'
        registered_date_str = user_info['registered_at']
        if 'T' in registered_date_str:
            registered_date = datetime.fromisoformat(registered_date_str.replace('Z', '+00:00'))
        else:
            registered_date = datetime.strptime(registered_date_str, "%Y-%m-%d %H:%M:%S")
        formatted_date = registered_date.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        formatted_date = user_info['registered_at']
    
    text += f"\n📅 Дата регистрации: {formatted_date}\n"
    text += f"🛒 Количество покупок: {purchases_count}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("payment_ready_"))
async def payment_ready(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик кнопки Готова - запрос скриншота"""
    product_id = int(callback.data.split("_")[2])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        return
    
    # Сохраняем информацию о заказе в состоянии
    await state.update_data(product_id=product_id)
    await state.set_state(PaymentStates.waiting_for_screenshot)
    
    text = "📸 Отправьте скриншот перевода в бота\n\n"
    text += f"🛍️ Товар: {product['name']}\n"
    text += f"💰 Сумма: {product['price']}₽\n\n"
    text += "Пожалуйста, отправьте скриншот подтверждения оплаты в виде фото.\n"
    text += "После отправки скриншота нажмите кнопку 'Отправить на проверку админу'."
    
    keyboard = get_send_to_admin_keyboard(product_id, product['category_id'])
    
    # Удаляем старое сообщение (с фото или без) и отправляем новое текстовое
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    # Сохраняем message_id нового сообщения для последующего обновления
    sent_message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text,
        reply_markup=keyboard
    )
    
    # Сохраняем message_id для последующего обновления
    await state.update_data(message_id=sent_message.message_id)
    
    await callback.answer()


@catalog_router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения скриншота оплаты - сохраняем в состоянии и обновляем сообщение"""
    data = await state.get_data()
    product_id = data.get('product_id')
    message_id = data.get('message_id')
    
    if not product_id:
        await message.answer("Ошибка: информация о заказе не найдена.")
        await state.clear()
        return
    
    product = db.get_product(product_id)
    if not product:
        await message.answer("Ошибка: товар не найден.")
        await state.clear()
        return
    
    # Сохраняем file_id фото в состоянии
    photo = message.photo[-1]  # Берем самое большое фото
    await state.update_data(screenshot_file_id=photo.file_id)
    
    # Удаляем сообщение со скриншотом
    try:
        await message.delete()
    except Exception:
        pass
    
    # Обновляем предыдущее сообщение
    text = "📸 Скриншот получен!\n\n"
    text += f"🛍️ Товар: {product['name']}\n"
    text += f"💰 Сумма: {product['price']}₽\n\n"
    text += "✅ Скриншот перевода получен.\n"
    text += "Нажмите кнопку 'Отправить на проверку админу' для отправки заказа."
    
    keyboard = get_send_to_admin_keyboard(product_id, product['category_id'])
    
    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
        except Exception:
            # Если не удалось обновить, отправляем новое сообщение
            sent_message = await bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )
            await state.update_data(message_id=sent_message.message_id)
    else:
        # Если message_id не найден, отправляем новое сообщение
        sent_message = await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        await state.update_data(message_id=sent_message.message_id)


@catalog_router.message(PaymentStates.waiting_for_screenshot)
async def receive_screenshot_invalid(message: Message, state: FSMContext):
    """Обработчик некорректного сообщения (не фото)"""
    await message.answer(
        "❌ Пожалуйста, отправьте скриншот перевода в виде фото.\n\n"
        "Если вы уже оплатили, прикрепите скриншот подтверждения оплаты."
    )


@catalog_router.callback_query(F.data.startswith("send_screenshot_"))
async def send_screenshot_to_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработчик кнопки Отправить на проверку админу"""
    product_id = int(callback.data.split("_")[2])
    product = db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден!", show_alert=True)
        await state.clear()
        return
    
    # Получаем сохраненный скриншот из состояния
    data = await state.get_data()
    screenshot_file_id = data.get('screenshot_file_id')
    
    if not screenshot_file_id:
        await callback.answer(
            "❌ Скриншот не найден! Пожалуйста, сначала отправьте скриншот перевода.",
            show_alert=True
        )
        return
    
    # Отправляем уведомление администраторам
    from config import ADMIN_IDS
    from keyboards import get_admin_payment_actions_keyboard
    
    # Получаем последний заказ пользователя для этого товара
    user_orders = db.get_user_orders(callback.from_user.id)
    current_order = None
    for order in user_orders:
        if order['product_id'] == product_id and order['status'] == 'pending':
            current_order = order
            break
    
    # Если заказ не найден, создаем новый
    if not current_order:
        order_id = db.create_order(
            user_id=callback.from_user.id,
            product_id=product_id,
            product_name=product['name'],
            price=product['price']
        )
        # Сохраняем screenshot_file_id в заказе
        if screenshot_file_id:
            db.update_order_screenshot(order_id, screenshot_file_id)
    else:
        order_id = current_order['id']
        # Обновляем screenshot_file_id если его еще нет
        if screenshot_file_id and not current_order.get('screenshot_file_id'):
            db.update_order_screenshot(order_id, screenshot_file_id)
    
    notification_text = f"📸 Новый скриншот оплаты\n\n"
    notification_text += f"👤 Пользователь: {callback.from_user.first_name}"
    if callback.from_user.username:
        notification_text += f" (@{callback.from_user.username})"
    notification_text += f"\n🆔 ID: {callback.from_user.id}\n\n"
    notification_text += f"🛍️ Товар: {product['name']}\n"
    notification_text += f"💰 Сумма: {product['price']}₽\n"
    notification_text += f"📋 Заказ ID: {order_id}"
    
    # Отправляем уведомления админам с кнопками и сохраняем message_id
    sent_to_admins = False
    for admin_id in ADMIN_IDS:
        try:
            sent_message = await bot.send_photo(
                chat_id=admin_id,
                photo=screenshot_file_id,
                caption=notification_text,
                reply_markup=get_admin_payment_actions_keyboard(order_id, callback.from_user.id)
            )
            # Сохраняем message_id для последующего обновления
            db.update_admin_message_id(order_id, admin_id, sent_message.message_id)
            sent_to_admins = True
        except Exception:
            pass  # Игнорируем ошибки отправки админам
    
    if sent_to_admins:
        # Обновляем сообщение с подтверждением
        try:
            await callback.message.edit_text(
                "✅ Заказ отправлен на проверку!\n\n"
                f"🛍️ Товар: {product['name']}\n"
                f"💰 Сумма: {product['price']}₽\n\n"
                "Администратор проверит оплату и свяжется с вами в ближайшее время.",
                reply_markup=get_back_to_shop_keyboard()
            )
        except Exception:
            # Если не удалось обновить, отправляем новое сообщение
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text="✅ Заказ отправлен на проверку!\n\n"
                     f"🛍️ Товар: {product['name']}\n"
                     f"💰 Сумма: {product['price']}₽\n\n"
                     "Администратор проверит оплату и свяжется с вами в ближайшее время.",
                reply_markup=get_back_to_shop_keyboard()
            )
        await callback.answer("Заказ отправлен администратору!", show_alert=True)
    else:
        await callback.answer(
            "⚠️ Не удалось отправить заказ. Попробуйте позже.",
            show_alert=True
        )
    
    await state.clear()


# Обработка email и кода от пользователя
@catalog_router.message(F.text.regexp(r'^[^@]+@[^@]+\.[^@]+$'))
async def receive_email_auto(message: Message, state: FSMContext, bot: Bot):
    """Автоматически обработать email если пользователь имеет активный заказ"""
    user_id = message.from_user.id
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    # Если уже в состоянии ожидания email, обрабатываем
    if current_state == UserOrderStates.waiting_for_email:
        data = await state.get_data()
        order_id = data.get('order_id')
        
        if order_id:
            email = message.text.strip()
            
            # Удаляем сообщение пользователя
            try:
                await message.delete()
            except Exception:
                pass
            
            # Сохраняем email в базе данных
            db.update_order_email(order_id, email)
            
            # Обновляем сообщение админу
            from handlers.admin import update_admin_order_message, update_user_order_message
            from config import ADMIN_IDS
            
            for admin_id in ADMIN_IDS:
                try:
                    await update_admin_order_message(bot, order_id, user_id, admin_id)
                except Exception:
                    pass
            
            # Обновляем сообщение пользователю (редактируем существующее)
            await update_user_order_message(bot, order_id, user_id)
            
            await state.clear()
            return
    
    # Проверяем, есть ли у пользователя активный заказ со статусом confirmed без email
    user_orders = db.get_user_orders(user_id)
    active_order = None
    for order in user_orders:
        if order['status'] == 'confirmed' and not order.get('email'):
            active_order = order
            break
    
    if active_order:
        email = message.text.strip()
        order_id = active_order['id']
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except Exception:
            pass
        
        # Сохраняем email в базе данных
        db.update_order_email(order_id, email)
        
        # Обновляем сообщение админу
        from handlers.admin import update_admin_order_message, update_user_order_message
        from config import ADMIN_IDS
        
        for admin_id in ADMIN_IDS:
            try:
                await update_admin_order_message(bot, order_id, user_id, admin_id)
            except Exception:
                pass
        
        # Обновляем сообщение пользователю (редактируем существующее)
        await update_user_order_message(bot, order_id, user_id)
        
        await state.clear()


@catalog_router.message(UserOrderStates.waiting_for_email)
async def receive_email(message: Message, state: FSMContext, bot: Bot):
    """Получить email от пользователя"""
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id:
        # Пытаемся найти активный заказ
        user_orders = db.get_user_orders(message.from_user.id)
        active_order = None
        for order in user_orders:
            if order['status'] == 'confirmed' and not order.get('email'):
                active_order = order
                break
        
        if not active_order:
            await message.answer("Ошибка: информация о заказе не найдена.")
            await state.clear()
            return
        
        order_id = active_order['id']
        await state.update_data(order_id=order_id)
    
    email = message.text.strip()
    
    # Простая проверка email
    if '@' not in email or '.' not in email.split('@')[1]:
        await message.answer("❌ Неверный формат email. Пожалуйста, введите корректный email адрес.")
        return
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass
    
    # Сохраняем email в базе данных
    db.update_order_email(order_id, email)
    
    # Обновляем сообщение админу
    from handlers.admin import update_admin_order_message, update_user_order_message
    from config import ADMIN_IDS
    
    for admin_id in ADMIN_IDS:
        try:
            await update_admin_order_message(bot, order_id, message.from_user.id, admin_id)
        except Exception:
            pass
    
    # Обновляем сообщение пользователю (редактируем существующее)
    await update_user_order_message(bot, order_id, message.from_user.id)
    
    await state.clear()




@catalog_router.message(UserOrderStates.waiting_for_code)
async def receive_code(message: Message, state: FSMContext, bot: Bot):
    """Получить код от пользователя"""
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id:
        # Пытаемся найти активный заказ с email но без кода
        user_orders = db.get_user_orders(message.from_user.id)
        active_order = None
        for order in user_orders:
            if order['status'] == 'confirmed' and order.get('email') and not order.get('code'):
                active_order = order
                break
        
        if not active_order:
            await message.answer("Ошибка: информация о заказе не найдена.")
            await state.clear()
            return
        
        order_id = active_order['id']
        await state.update_data(order_id=order_id)
    
    code = message.text.strip()
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass
    
    # Сохраняем код в базе данных
    db.update_order_code(order_id, code)
    
    order = db.get_order(order_id)
    if not order:
        await message.answer("Ошибка: заказ не найден.")
        await state.clear()
        return
    
    # Обновляем сообщение админу
    from handlers.admin import update_admin_order_message, update_user_order_message
    from config import ADMIN_IDS
    
    for admin_id in ADMIN_IDS:
        try:
            await update_admin_order_message(bot, order_id, message.from_user.id, admin_id)
        except Exception:
            pass
    
    # Обновляем сообщение пользователю (редактируем существующее)
    await update_user_order_message(bot, order_id, message.from_user.id)
    
    # Отправляем финальное сообщение о том, что нужно ждать
    await bot.send_message(
        chat_id=message.from_user.id,
        text="✅ Данные отправлены администратору!\n\n"
             
    )
    
    await state.clear()


# Обработчик для автоматического определения состояния при получении кода
@catalog_router.message(F.text & ~F.text.startswith('/'))
async def handle_text_message(message: Message, state: FSMContext, bot: Bot):
    """Обработчик текстовых сообщений для автоматического определения состояния"""
    current_state = await state.get_state()
    user_id = message.from_user.id
    
    # Если не в состоянии ожидания кода, проверяем активные заказы
    if current_state != UserOrderStates.waiting_for_code:
        # Проверяем, есть ли заказ со статусом confirmed с email но без кода
        user_orders = db.get_user_orders(user_id)
        active_order = None
        for order in user_orders:
            if order['status'] == 'confirmed' and order.get('email') and not order.get('code'):
                active_order = order
                break
        
        if active_order:
            # Устанавливаем состояние и обрабатываем как код
            await state.update_data(order_id=active_order['id'])
            await state.set_state(UserOrderStates.waiting_for_code)
            
            code = message.text.strip()
            order_id = active_order['id']
            
            # Удаляем сообщение пользователя
            try:
                await message.delete()
            except Exception:
                pass
            
            # Сохраняем код в базе данных
            db.update_order_code(order_id, code)
            
            order = db.get_order(order_id)
            if not order:
                await message.answer("Ошибка: заказ не найден.")
                await state.clear()
                return
            
            # Обновляем сообщение админу
            from handlers.admin import update_admin_order_message, update_user_order_message
            from config import ADMIN_IDS
            
            for admin_id in ADMIN_IDS:
                try:
                    await update_admin_order_message(bot, order_id, message.from_user.id, admin_id)
                except Exception:
                    pass
            
            # Обновляем сообщение пользователю (редактируем существующее)
            await update_user_order_message(bot, order_id, message.from_user.id)
            
            # Отправляем финальное сообщение о том, что нужно ждать
            await bot.send_message(
                chat_id=message.from_user.id,
                text="✅ Данные отправлены администратору!\n\n"
                     
            )
            
            await state.clear()


@catalog_router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    is_admin = callback.from_user.id in ADMIN_IDS
    
    await callback.message.edit_text(
        "👋 Добро пожаловать в магазин Brawl Stars!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )
    await callback.answer()
