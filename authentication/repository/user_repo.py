__all__ = ["user_repo"]

import os
import sqlite3
from sqlite3 import Error

from settings.settings import BASE_DIR

tables = """ CREATE TABLE IF NOT EXISTS `users`(
    `id` integer PRIMARY KEY AUTOINCREMENT,
    `username` text,
    `email` text NOT NULL,
    `password` text NOT NULL,
    `last_login` text NOT NULL,
    `date_joined` text,
    `is_active` integer DEFAULT 1,
    `is_admin` integer DEFAULT 0
    ); """

users_list = """ SELECT * FROM users """

insert_user = """ INSERT INTO users(username, email, password, last_login, date_joined)
            VALUES(?,?,?,?,?)"""

user_by_mail = """ SELECT * FROM users WHERE email = ? """

update_last_user_login = """ UPDATE users SET last_login = ?  WHERE id = ? """

update_user_active = """ UPDATE users SET is_active = ?  WHERE id = ? """

delete_user = """ DELETE FROM users WHERE id = ? """


class DatabaseConnection:
    """manage database"""

    conn = None

    def __init__(self) -> None:
        self.conn = self.create_connection()

    def create_connection(self):
        database = os.path.join(BASE_DIR, "data.db")
        try:
            self.conn = sqlite3.connect(database)
        except Error as err:
            raise err
        return self.conn

    def close_connection(self):
        self.conn.close()

    def create_table(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            self.conn.commit()
            self.conn.close()
        except Error as err:
            raise err

    def swap_database(self):
        """here to swap dev and prod database"""
        pass


class UserRepository:
    """Define user request"""

    def __init__(self, database: DatabaseConnection):
        self.database = database

    def get_user_by_email(self, email):
        cur = self.database.conn.cursor()
        cur.execute(user_by_mail, (email,))
        self.database.conn.commit()
        rows = cur.fetchone()
        return rows

    def get_all_users(self):
        cur = self.database.conn.cursor()
        cur.execute(users_list)
        self.database.conn.commit()
        rows = cur.fetchall()
        return rows

    def is_user_exists():
        pass

    def create_user(self, args):
        cur = self.database.conn.cursor()
        cur.execute(insert_user, args)
        self.database.conn.commit()

    def update_user_last_login(self, user_id, last_login):
        cur = self.database.conn.cursor()
        cur.execute(update_last_user_login, (last_login, user_id))
        self.database.conn.commit()

    def update_user_is_active(self, user_id, active_num):
        cur = self.database.conn.cursor()
        cur.execute(update_user_active, (active_num, user_id))
        self.database.conn.commit()

    def delete_user(self, user_id):
        cur = self.database.conn.cursor()
        cur.execute(delete_user, (user_id,))
        self.database.conn.commit()


if __name__ == "__main__":
    db = DatabaseConnection().create_table(query=tables)
    from datetime import datetime

    def get_time_today():
        """get current date time"""
        return datetime.now().strftime("%d-%m-%Y %H:%M:%S")
