from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from database import db
from keyboards import (
    get_admin_keyboard,
    get_admin_categories_keyboard,
    get_admin_products_keyboard,
    get_cancel_keyboard,
    get_category_selection_keyboard,
    get_main_menu_keyboard,
    get_admin_payment_actions_keyboard,
    get_order_processing_keyboard,
    get_order_email_received_keyboard,
    get_order_code_received_keyboard
)
from config import ADMIN_IDS

admin_router = Router()


async def update_user_order_message(bot: Bot, order_id: int, user_id: int, request_code: bool = False):
    """Обновить сообщение пользователю о заказе (запрос email/кода)
    
    Args:
        bot: Экземпляр бота
        order_id: ID заказа
        user_id: ID пользователя
        request_code: True если администратор явно запросил код, False иначе
    """
    order = db.get_order(order_id)
    if not order:
        return
    
    # Формируем текст сообщения
    text = f"📧 Требуется email для входа\n\n"
    text += f"🛍️ Товар: {order['product_name']}\n\n"
    
    if order.get('email'):
        text += f"✅ Email получен: {order['email']}\n\n"
        if order.get('code'):
            text += f"✅ Код получен: {order['code']}\n\n"
            text += "Ожидайте подтверждения от администратора."
        elif request_code:
            # Показываем запрос кода только если администратор явно запросил
            text += "Пожалуйста, отправьте код подтверждения."
        else:
            # Если email получен, но код не запрошен - просто подтверждаем получение email
            text += "Ожидайте дальнейших инструкций от администратора."
    else:
        text += "Пожалуйста, отправьте ваш email адрес для входа в игру."
    
    # Удаляем старое сообщение и отправляем новое (для уведомлений Telegram)
    user_message_id = order.get('user_message_id')
    
    # Удаляем старое сообщение если оно существует
    if user_message_id:
        try:
            await bot.delete_message(
                chat_id=user_id,
                message_id=user_message_id
            )
        except Exception:
            # Игнорируем ошибки удаления (сообщение могло быть уже удалено)
            pass
    
    # Отправляем новое сообщение
    try:
        sent_message = await bot.send_message(
            chat_id=user_id,
            text=text
        )
        # Сохраняем message_id
        db.update_user_message_id(order_id, sent_message.message_id)
    except Exception:
        pass


async def update_admin_order_message(bot: Bot, order_id: int, user_id: int, admin_id: int):
    """Обновить сообщение админу о заказе со всей информацией"""
    order = db.get_order(order_id)
    if not order:
        return
    
    # Получаем информацию о пользователе
    user_info = db.get_user(user_id)
    user_name = user_info.get('first_name', 'Пользователь') if user_info else 'Пользователь'
    username = user_info.get('username', '') if user_info else ''
    
    # Формируем полный текст сообщения
    text = f"📸 Новый скриншот оплаты\n\n"
    text += f"👤 Пользователь: {user_name}"
    if username:
        text += f" (@{username})"
    text += f"\n🆔 ID: {user_id}\n\n"
    text += f"🛍️ Товар: {order['product_name']}\n"
    text += f"💰 Сумма: {order['price']}₽\n"
    text += f"📋 Заказ ID: {order_id}\n"
    
    # Добавляем статусы
    if order['status'] == 'confirmed':
        text += "\n✅ Оплата подтверждена администратором"
    
    if order.get('email'):
        text += f"\n📧 Email: {order['email']}"
    elif order['status'] == 'confirmed':
        text += "\n📧 Запрос email отправлен пользователю"
    
    if order.get('code'):
        text += f"\n🔑 Код: {order['code']}"
    elif order.get('email') and order['status'] == 'confirmed':
        text += "\n🔑 Запрос кода отправлен пользователю"
    
    if order['status'] == 'completed':
        text += "\n✅ Заказ выполнен"
    elif order['status'] == 'rejected':
        text += "\n❌ Оплата отклонена"
    
    # Определяем клавиатуру в зависимости от состояния
    keyboard = None
    if order['status'] == 'pending':
        keyboard = get_admin_payment_actions_keyboard(order_id, user_id)
    elif order['status'] == 'confirmed' and not order.get('email'):
        keyboard = get_order_processing_keyboard(order_id, user_id)
    elif order['status'] == 'confirmed' and order.get('email') and not order.get('code'):
        keyboard = get_order_email_received_keyboard(order_id, user_id)
    elif order['status'] == 'confirmed' and order.get('email') and order.get('code'):
        keyboard = get_order_code_received_keyboard(order_id, user_id)
    # Для completed и rejected клавиатура не нужна (None)
    
    # Удаляем старое сообщение и отправляем новое (для уведомлений Telegram)
    admin_message_id = order.get('admin_message_id')
    admin_chat_id = order.get('admin_chat_id')
    screenshot_file_id = order.get('screenshot_file_id')
    
    # Удаляем старое сообщение если оно существует для этого админа
    if admin_message_id and admin_chat_id == admin_id:
        try:
            await bot.delete_message(
                chat_id=admin_chat_id,
                message_id=admin_message_id
            )
        except Exception:
            # Игнорируем ошибки удаления (сообщение могло быть уже удалено)
            pass
    
    # Отправляем новое сообщение
    try:
        if screenshot_file_id:
            sent_message = await bot.send_photo(
                chat_id=admin_id,
                photo=screenshot_file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            sent_message = await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=keyboard
            )
        # Сохраняем новый message_id
        db.update_admin_message_id(order_id, admin_id, sent_message.message_id)
    except Exception:
        pass


class AddCategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()


class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_image = State()


class OrderProcessingStates(StatesGroup):
    waiting_for_email_confirmation = State()
    waiting_for_code_confirmation = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    
    await message.answer(
        "🔧 Админ панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


@admin_router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Показать админ панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "🔧 Админ панель\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard()
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await callback.answer()


@admin_router.callback_query(F.data == "back_to_main")
async def admin_back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню из админ панели"""
    is_admin_user = is_admin(callback.from_user.id)
    
    try:
        await callback.message.edit_text(
            "👋 Добро пожаловать в магазин Brawl Stars!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin_user)
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await callback.answer()


# Добавление категории
@admin_router.callback_query(F.data == "admin_add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """Начать добавление категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "➕ Добавление категории\n\n"
            "Введите название категории:",
            reply_markup=get_cancel_keyboard()
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await state.set_state(AddCategoryStates.waiting_for_name)
    await callback.answer()


@admin_router.callback_query(F.data == "cancel_action")
async def cancel_action_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена действия через callback"""
    await state.clear()
    try:
        await callback.message.edit_text(
            "🔧 Админ панель\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard()
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await callback.answer("Действие отменено")


@admin_router.message(Command("cancel"))
async def cancel_action_message(message: Message, state: FSMContext):
    """Отмена действия через команду /cancel"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return
    
    await state.clear()
    await message.answer(
        "🔧 Админ панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )


@admin_router.message(AddCategoryStates.waiting_for_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    await state.update_data(name=message.text)
    await message.answer(
        "Введите описание категории (или отправьте '-' чтобы пропустить):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddCategoryStates.waiting_for_description)


@admin_router.message(AddCategoryStates.waiting_for_description)
async def process_category_description(message: Message, state: FSMContext):
    """Обработка описания категории"""
    data = await state.get_data()
    description = None if message.text == "-" else message.text
    
    category_id = db.add_category(data['name'], description)
    
    await message.answer(
        f"✅ Категория '{data['name']}' успешно добавлена!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()


# Добавление товара
@admin_router.callback_query(F.data == "admin_add_product")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    categories = db.get_all_categories()
    
    if not categories:
        await callback.answer(
            "Сначала добавьте хотя бы одну категорию!",
            show_alert=True
        )
        return
    
    try:
        await callback.message.edit_text(
            "➕ Добавление товара\n\n"
            "Выберите категорию:",
            reply_markup=get_category_selection_keyboard(categories)
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await state.set_state(AddProductStates.waiting_for_category)
    await callback.answer()


@admin_router.callback_query(
    AddProductStates.waiting_for_category,
    F.data.startswith("select_category_")
)
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории для товара"""
    # Формат: select_category_123 -> ["select", "category", "123"]
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    
    try:
        await callback.message.edit_text(
            "Введите название товара:",
            reply_markup=get_cancel_keyboard()
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await state.set_state(AddProductStates.waiting_for_name)
    await callback.answer()


@admin_router.message(AddProductStates.waiting_for_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    await state.update_data(name=message.text)
    await message.answer(
        "Введите цену товара (только число):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_price)


@admin_router.message(AddProductStates.waiting_for_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        await message.answer(
            "Введите описание товара (или отправьте '-' чтобы пропустить):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AddProductStates.waiting_for_description)
    except ValueError:
        await message.answer("❌ Неверный формат цены! Введите число:")


@admin_router.message(AddProductStates.waiting_for_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    data = await state.get_data()
    description = None if message.text == "-" else message.text
    await state.update_data(description=description)
    
    await message.answer(
        "📷 Отправьте фото товара или URL изображения\n"
        "(или отправьте '-' чтобы пропустить):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_image)


@admin_router.message(AddProductStates.waiting_for_image, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Обработка фото товара"""
    data = await state.get_data()
    
    # Получаем file_id самого большого фото
    photo = message.photo[-1]
    photo_file_id = photo.file_id
    
    product_id = db.add_product(
        category_id=data['category_id'],
        name=data['name'],
        price=data['price'],
        description=data.get('description'),
        image_url=None,
        photo_file_id=photo_file_id
    )
    
    await message.answer(
        f"✅ Товар '{data['name']}' успешно добавлен с фото!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()


@admin_router.message(AddProductStates.waiting_for_image)
async def process_product_image(message: Message, state: FSMContext):
    """Обработка изображения товара (URL или пропуск)"""
    data = await state.get_data()
    image_url = None if message.text == "-" else message.text
    
    product_id = db.add_product(
        category_id=data['category_id'],
        name=data['name'],
        price=data['price'],
        description=data.get('description'),
        image_url=image_url,
        photo_file_id=None
    )
    
    await message.answer(
        f"✅ Товар '{data['name']}' успешно добавлен!",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()


# Список категорий
@admin_router.callback_query(F.data == "admin_list_categories")
async def list_categories(callback: CallbackQuery):
    """Показать список категорий"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    categories = db.get_all_categories()
    
    if not categories:
        try:
            await callback.message.edit_text(
                "📋 Список категорий пуст.",
                reply_markup=get_admin_keyboard()
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass
        await callback.answer()
        return
    
    text = "📋 Список категорий:\n\n"
    for cat in categories:
        text += f"• {cat['name']}\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_categories_keyboard(categories)
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await callback.answer()


# Удаление категории
@admin_router.callback_query(F.data.startswith("admin_delete_category_"))
async def delete_category(callback: CallbackQuery):
    """Удалить категорию"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[3])
    category = db.get_category(category_id)
    
    if category:
        db.delete_category(category_id)
        await callback.answer(f"Категория '{category['name']}' удалена!", show_alert=True)
    else:
        await callback.answer("Категория не найдена!", show_alert=True)
    
    # Обновить список
    categories = db.get_all_categories()
    if categories:
        text = "📋 Список категорий:\n\n"
        for cat in categories:
            text += f"• {cat['name']}\n"
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_admin_categories_keyboard(categories)
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass
    else:
        try:
            await callback.message.edit_text(
                "📋 Список категорий пуст.",
                reply_markup=get_admin_keyboard()
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass


# Список товаров
@admin_router.callback_query(F.data == "admin_list_products")
async def list_products(callback: CallbackQuery):
    """Показать список товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    products = db.get_all_products()
    
    if not products:
        try:
            await callback.message.edit_text(
                "📋 Список товаров пуст.",
                reply_markup=get_admin_keyboard()
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass
        await callback.answer()
        return
    
    text = "📋 Список товаров:\n\n"
    for product in products:
        category = db.get_category(product['category_id'])
        text += f"• {product['name']} ({category['name']}) - {product['price']}₽\n"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_products_keyboard(products)
        )
    except TelegramBadRequest:
        # Сообщение не изменилось, это нормально
        pass
    await callback.answer()


# Обработка оплат от пользователей
@admin_router.callback_query(F.data.startswith("admin_confirm_payment_"))
async def confirm_payment(callback: CallbackQuery, bot: Bot):
    """Подтвердить оплату от пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Формат: admin_confirm_payment_{order_id}_{user_id}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    # Обновляем статус заказа
    db.update_order_status(order_id, 'confirmed')
    
    # Обновляем сообщение админу
    await update_admin_order_message(bot, order_id, user_id, callback.from_user.id)
    
    await callback.answer("Оплата подтверждена!", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_reject_payment_"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    """Отклонить оплату - оплата не поступила"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Формат: admin_reject_payment_{order_id}_{user_id}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    # Обновляем статус заказа
    db.update_order_status(order_id, 'rejected')
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"❌ Оплата не подтверждена\n\n"
                 f"🛍️ Товар: {order['product_name']}\n"
                 f"💰 Сумма: {order['price']}₽\n\n"
                 f"К сожалению, оплата не поступила. "
                 f"Пожалуйста, проверьте правильность реквизитов и попробуйте снова."
        )
    except Exception:
        pass  # Игнорируем ошибки отправки пользователю
    
    # Обновляем сообщение админу
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n❌ Оплата отклонена администратором",
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ Оплата отклонена администратором",
                reply_markup=None
            )
    except Exception:
        pass
    
    await callback.answer("Оплата отклонена! Пользователь уведомлен.", show_alert=True)


# Обработка заказа после подтверждения оплаты
@admin_router.callback_query(F.data.startswith("admin_request_email_"))
async def request_email(callback: CallbackQuery, bot: Bot):
    """Запросить email у пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Формат: admin_request_email_{order_id}_{user_id}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    # Обновляем сообщение пользователю (редактируем существующее или отправляем новое)
    await update_user_order_message(bot, order_id, user_id)
    
    # Обновляем сообщение админу
    await update_admin_order_message(bot, order_id, user_id, callback.from_user.id)
    
    await callback.answer("Запрос email отправлен пользователю", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_request_code_"))
async def request_code(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Запросить код у пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Формат: admin_request_code_{order_id}_{user_id}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    # Проверяем, что email уже получен
    if not order.get('email'):
        await callback.answer("Сначала нужно получить email от пользователя!", show_alert=True)
        return
    
    # Обновляем сообщение пользователю (редактируем существующее или отправляем новое)
    # Передаем request_code=True, чтобы показать запрос кода
    await update_user_order_message(bot, order_id, user_id, request_code=True)
    
    # Обновляем сообщение админу
    await update_admin_order_message(bot, order_id, user_id, callback.from_user.id)
    
    await callback.answer("Запрос кода отправлен пользователю", show_alert=True)


@admin_router.callback_query(F.data.startswith("admin_complete_order_"))
async def complete_order(callback: CallbackQuery, bot: Bot):
    """Завершить заказ"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Формат: admin_complete_order_{order_id}_{user_id}
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    order = db.get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    # Обновляем статус заказа
    db.update_order_status(order_id, 'completed')
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Заказ выполнен!\n\n"
                 f"🛍️ Товар: {order['product_name']}\n"
                 f"💰 Сумма: {order['price']}₽\n\n"
                 f"Спасибо за покупку! Наслаждайтесь игрой!"
        )
    except Exception:
        pass
    
    # Обновляем сообщение админу
    await update_admin_order_message(bot, order_id, user_id, callback.from_user.id)
    
    await callback.answer("Заказ завершен! Пользователь уведомлен.", show_alert=True)


# Удаление товара
@admin_router.callback_query(F.data.startswith("admin_delete_product_"))
async def delete_product(callback: CallbackQuery):
    """Удалить товар"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[3])
    product = db.get_product(product_id)
    
    if product:
        db.delete_product(product_id)
        await callback.answer(f"Товар '{product['name']}' удален!", show_alert=True)
    else:
        await callback.answer("Товар не найден!", show_alert=True)
    
    # Обновить список
    products = db.get_all_products()
    if products:
        text = "📋 Список товаров:\n\n"
        for p in products:
            category = db.get_category(p['category_id'])
            text += f"• {p['name']} ({category['name']}) - {p['price']}₽\n"
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_admin_products_keyboard(products)
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass
    else:
        try:
            await callback.message.edit_text(
                "📋 Список товаров пуст.",
                reply_markup=get_admin_keyboard()
            )
        except TelegramBadRequest:
            # Сообщение не изменилось, это нормально
            pass
