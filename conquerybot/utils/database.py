import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Błąd podczas łączenia z bazą danych: {e}")
        return None

def init_database():
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Tworzenie tabeli użytkowników
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    guild_id BIGINT,
                    xp INT DEFAULT 0,
                    level INT DEFAULT 1,
                    wallet INT DEFAULT 0,
                    bank INT DEFAULT 0,
                    last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_user_guild (user_id, guild_id)
                )
            """)
            
            # Tworzenie tabeli sklepu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shop (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    guild_id BIGINT,
                    item_name VARCHAR(255),
                    price INT,
                    description TEXT,
                    UNIQUE KEY unique_item_guild (item_name, guild_id)
                )
            """)
            
            connection.commit()
            print("Baza danych zainicjalizowana pomyślnie!")
            
        except Error as e:
            print(f"Błąd podczas inicjalizacji bazy danych: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def get_user_data(user_id: int, guild_id: int):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM users 
                WHERE user_id = %s AND guild_id = %s
            """, (user_id, guild_id))
            result = cursor.fetchone()
            
            if not result:
                # Jeśli użytkownik nie istnieje, utwórz go
                cursor.execute("""
                    INSERT INTO users (user_id, guild_id)
                    VALUES (%s, %s)
                """, (user_id, guild_id))
                connection.commit()
                return {'user_id': user_id, 'guild_id': guild_id, 'xp': 0, 'level': 1, 'wallet': 0, 'bank': 0}
            
            return result
            
        except Error as e:
            print(f"Błąd podczas pobierania danych użytkownika: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def update_user_data(user_id: int, guild_id: int, wallet: int = None, bank: int = None, xp: int = None, level: int = None):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            updates = []
            values = []
            
            if wallet is not None:
                updates.append("wallet = %s")
                values.append(wallet)
            if bank is not None:
                updates.append("bank = %s")
                values.append(bank)
            if xp is not None:
                updates.append("xp = %s")
                values.append(xp)
            if level is not None:
                updates.append("level = %s")
                values.append(level)
            
            if updates:
                values.extend([user_id, guild_id])
                query = f"""
                    UPDATE users 
                    SET {', '.join(updates)}
                    WHERE user_id = %s AND guild_id = %s
                """
                cursor.execute(query, values)
                connection.commit()
                
        except Error as e:
            print(f"Błąd podczas aktualizacji danych użytkownika: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def get_shop_items(guild_id: int):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM shop 
                WHERE guild_id = %s
            """, (guild_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Błąd podczas pobierania przedmiotów ze sklepu: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def add_shop_item(guild_id: int, item_name: str, price: int, description: str):
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO shop (guild_id, item_name, price, description)
                VALUES (%s, %s, %s, %s)
            """, (guild_id, item_name, price, description))
            connection.commit()
            return True
        except Error as e:
            print(f"Błąd podczas dodawania przedmiotu do sklepu: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close() 