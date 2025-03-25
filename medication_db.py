# medication_db.py
import sqlite3
from contextlib import closing

DB_NAME = "medications.db"

# DB없다면 DB 생성하기
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:

            # 약섭취 스케쥴 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medication_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine TEXT NOT NULL,
                    socket TEXT NOT NULL,
                    morning BOOLEAN DEFAULT 0,
                    lunch BOOLEAN DEFAULT 0,
                    dinner BOOLEAN DEFAULT 0
                )
            ''')

            # 약섭취 여부 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medication_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine TEXT NOT NULL,
                    socket TEXT NOT NULL,
                    morning BOOLEAN DEFAULT 0,
                    lunch BOOLEAN DEFAULT 0,
                    dinner BOOLEAN DEFAULT 0
                )
            ''')

            # 물품 보관 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS socket_contents (
                    socket TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            ''')
            conn.commit()

# 약 섭취 스케쥴 추가
def add_schedule(medicine, socket, morning=False, lunch=False, dinner=False):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('INSERT INTO medication_schedule (medicine, socket, morning, lunch, dinner) VALUES (?, ?, ?, ?, ?)',
                           (medicine, socket, morning, lunch, dinner))
            conn.commit()

# 약 스케쥴 수정 (사용 안할 수도 있음)
def update_schedule(med_id, morning=None, lunch=None, dinner=None):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            fields = []
            values = []
            if morning is not None:
                fields.append("morning = ?")
                values.append(morning)
            if lunch is not None:
                fields.append("lunch = ?")
                values.append(lunch)
            if dinner is not None:
                fields.append("dinner = ?")
                values.append(dinner)
            if not fields:
                return
            values.append(med_id)
            query = f'UPDATE medication_schedule SET {", ".join(fields)} WHERE id = ?'
            cursor.execute(query, values)
            conn.commit()

# 약 스케쥴 삭제
def delete_schedule(med_id):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('DELETE FROM medication_schedule WHERE id = ?', (med_id,))
            conn.commit()

# 모든 스케쥴 출력
def get_all_schedules():
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM medication_schedule')
            return cursor.fetchall()

# 약 섭취여부 추가
def add_status(medicine, socket, morning=False, lunch=False, dinner=False):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('INSERT INTO medication_status (medicine, socket, morning, lunch, dinner) VALUES (?, ?, ?, ?, ?)',
                           (medicine, socket, morning, lunch, dinner))
            conn.commit()

# 약 섭취 여부 업데이트
def update_status(med_id, morning=None, lunch=None, dinner=None):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            fields = []
            values = []
            if morning is not None:
                fields.append("morning = ?")
                values.append(morning)
            if lunch is not None:
                fields.append("lunch = ?")
                values.append(lunch)
            if dinner is not None:
                fields.append("dinner = ?")
                values.append(dinner)
            if not fields:
                return
            values.append(med_id)
            query = f'UPDATE medication_status SET {", ".join(fields)} WHERE id = ?'
            cursor.execute(query, values)
            conn.commit()

# 모든 오늘 약 섭취여부 출력
def get_all_statuses():
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT * FROM medication_status')
            return cursor.fetchall()

# 소켓 정보 추가
def add_socket_content(socket, name):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('INSERT INTO socket_contents (socket, name) VALUES (?, ?)', (socket, name))
            conn.commit()

# 소켓 정보 삭제
def delete_socket_content(socket):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('DELETE FROM socket_contents WHERE socket = ?', (socket,))
            conn.commit()

# 소켓 정보 조회
def get_socket_content(socket):
    with sqlite3.connect(DB_NAME) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute('SELECT name FROM socket_contents WHERE socket = ?', (socket,))
            result = cursor.fetchone()
            return result[0] if result else None