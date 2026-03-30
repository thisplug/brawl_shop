from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню с кнопкой Каталог"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📦 Каталог",
                callback_data="show_catalog"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="show_profile"
            )
        ]
    ]
    
    if is_admin:
        keyboard.append([
            InlineKeyboardButton(
                text="🔧 Админ панель",
                callback_data="admin_panel"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_shop_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возврата в магазин"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🏪 Вернуться в магазин",
                callback_data="back_to_main"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_keyboard(categories: List[Dict], is_admin: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура каталога с категориями"""
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category['name'],
                callback_data=f"category_{category['id']}"
            )
        ])
    
    # Кнопка "Назад в главное меню"
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Главное меню",
            callback_data="back_to_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_keyboard(category_id: int, products: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура категории с товарами"""
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']}₽",
                callback_data=f"product_{product['id']}"
            )
        ])
    
    # Кнопка "Назад к каталогу"
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад к каталогу",
            callback_data="back_to_catalog"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура товара"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛒 Купить",
                callback_data=f"buy_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к категории",
                callback_data=f"category_{category_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_methods_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="💳 Банковская карта",
                callback_data=f"payment_card_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📱 СБП (QR код)",
                callback_data=f"payment_qr_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"product_{product_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_ready_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после выбора способа оплаты с кнопкой Готова"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Готова",
                callback_data=f"payment_ready_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к категории",
                callback_data=f"category_{category_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_send_to_admin_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для отправки скриншота на проверку админу"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📤 Отправить на проверку админу",
                callback_data=f"send_screenshot_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к категории",
                callback_data=f"category_{category_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_payment_actions_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для администратора при проверке оплаты"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить оплату",
                callback_data=f"admin_confirm_payment_{order_id}_{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Оплата не поступила",
                callback_data=f"admin_reject_payment_{order_id}_{user_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_processing_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для обработки заказа после подтверждения оплаты"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📧 Запросить почту",
                callback_data=f"admin_request_email_{order_id}_{user_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_email_received_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после получения почты"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔑 Запросить код",
                callback_data=f"admin_request_code_{order_id}_{user_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_code_received_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура после получения кода"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Заказ выполнен",
                callback_data=f"admin_complete_order_{order_id}_{user_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_email_confirmation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения email пользователем"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить и отправить",
                callback_data=f"user_confirm_email_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Изменить",
                callback_data=f"user_change_email_{order_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ панели"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Добавить категорию",
                callback_data="admin_add_category"
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Добавить товар",
                callback_data="admin_add_product"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Список категорий",
                callback_data="admin_list_categories"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Список товаров",
                callback_data="admin_list_products"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="back_to_main"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура списка категорий для админа"""
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {category['name']}",
                callback_data=f"admin_edit_category_{category['id']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"admin_delete_category_{category['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin_panel"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_products_keyboard(products: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура списка товаров для админа"""
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {product['name']}",
                callback_data=f"admin_edit_product_{product['id']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"admin_delete_product_{product['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin_panel"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_selection_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории при добавлении товара"""
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category['name'],
                callback_data=f"select_category_{category['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_action"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="◀️ Главное меню",
            callback_data="back_to_main"
        )
    ]])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_action"
        )
    ]])
