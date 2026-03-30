import sqlite3
from typing import List, Optional, Tuple
from config import DATABASE_PATH


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Создание таблиц для категорий и товаров"""
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица категорий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                photo_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        
        # Добавляем колонку photo_file_id если её нет (для существующих БД)
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN photo_file_id TEXT")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # Таблица покупок/заказов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                email TEXT,
                code TEXT,
                screenshot_file_id TEXT,
                admin_message_id INTEGER,
                admin_chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            )
        """)
        
        # Добавляем колонки если их нет (для существующих БД)
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN code TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN screenshot_file_id TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN admin_message_id INTEGER")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN admin_chat_id INTEGER")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN user_message_id INTEGER")
        except sqlite3.OperationalError:
            pass
        
        self.conn.commit()

    # Методы для работы с категориями
    def add_category(self, name: str, description: Optional[str] = None) -> int:
        """Добавить категорию"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_all_categories(self) -> List[dict]:
        """Получить все категории"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_category(self, category_id: int) -> Optional[dict]:
        """Получить категорию по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_category(self, category_id: int, name: str, description: Optional[str] = None):
        """Обновить категорию"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE categories SET name = ?, description = ? WHERE id = ?",
            (name, description, category_id)
        )
        self.conn.commit()

    def delete_category(self, category_id: int):
        """Удалить категорию"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.conn.commit()

    # Методы для работы с товарами
    def add_product(self, category_id: int, name: str, price: float, 
                   description: Optional[str] = None, image_url: Optional[str] = None,
                   photo_file_id: Optional[str] = None) -> int:
        """Добавить товар"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO products (category_id, name, description, price, image_url, photo_file_id) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (category_id, name, description, price, image_url, photo_file_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_products_by_category(self, category_id: int) -> List[dict]:
        """Получить все товары категории, отсортированные по цене от меньшей к большей"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE category_id = ? ORDER BY price ASC",
            (category_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_product(self, product_id: int) -> Optional[dict]:
        """Получить товар по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_product(self, product_id: int, category_id: int, name: str, 
                      price: float, description: Optional[str] = None, 
                      image_url: Optional[str] = None, photo_file_id: Optional[str] = None):
        """Обновить товар"""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE products SET category_id = ?, name = ?, description = ?, 
               price = ?, image_url = ?, photo_file_id = ? WHERE id = ?""",
            (category_id, name, description, price, image_url, photo_file_id, product_id)
        )
        self.conn.commit()

    def delete_product(self, product_id: int):
        """Удалить товар"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()

    def get_all_products(self) -> List[dict]:
        """Получить все товары"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY category_id, name")
        return [dict(row) for row in cursor.fetchall()]

    # Методы для работы с пользователями
    def register_user(self, user_id: int, username: Optional[str] = None, 
                     first_name: Optional[str] = None, last_name: Optional[str] = None):
        """Зарегистрировать пользователя или обновить информацию"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, last_name))
        
        # Обновляем информацию если пользователь уже существует
        cursor.execute("""
            UPDATE users 
            SET username = ?, first_name = ?, last_name = ?
            WHERE user_id = ?
        """, (username, first_name, last_name, user_id))
        
        self.conn.commit()

    def get_user(self, user_id: int) -> Optional[dict]:
        """Получить информацию о пользователе"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_purchases_count(self, user_id: int) -> int:
        """Получить количество покупок пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0

    # Методы для работы с покупками
    def create_order(self, user_id: int, product_id: int, product_name: str, price: float) -> int:
        """Создать заказ/покупку"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, product_name, price, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (user_id, product_id, product_name, price))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_orders(self, user_id: int) -> List[dict]:
        """Получить все заказы пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_order(self, order_id: int) -> Optional[dict]:
        """Получить заказ по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_order_status(self, order_id: int, status: str):
        """Обновить статус заказа"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )
        self.conn.commit()

    def update_order_email(self, order_id: int, email: str):
        """Обновить email заказа"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET email = ? WHERE id = ?",
            (email, order_id)
        )
        self.conn.commit()

    def update_order_code(self, order_id: int, code: str):
        """Обновить код заказа"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET code = ? WHERE id = ?",
            (code, order_id)
        )
        self.conn.commit()

    def update_admin_message_id(self, order_id: int, admin_chat_id: int, admin_message_id: int):
        """Сохранить message_id сообщения админу для обновления"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET admin_chat_id = ?, admin_message_id = ? WHERE id = ?",
            (admin_chat_id, admin_message_id, order_id)
        )
        self.conn.commit()

    def update_order_screenshot(self, order_id: int, screenshot_file_id: str):
        """Сохранить file_id скриншота оплаты"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET screenshot_file_id = ? WHERE id = ?",
            (screenshot_file_id, order_id)
        )
        self.conn.commit()

    def update_user_message_id(self, order_id: int, user_message_id: int):
        """Сохранить message_id сообщения пользователю для обновления"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE orders SET user_message_id = ? WHERE id = ?",
            (user_message_id, order_id)
        )
        self.conn.commit()

    def close(self):
        """Закрыть соединение с БД"""
        self.conn.close()


# Глобальный экземпляр БД
db = Database()
