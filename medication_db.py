import psycopg2
from contextlib import closing
import os

# PostgreSQL connection string
DB_CONNECTION_STRING = os.getenv("POSTGRESQL_CONNECTION_STRING", "postgresql://abcd:1234@111.111.11.111:5432/userdb")

# Function to establish PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(DB_CONNECTION_STRING)

# DB initialization for PostgreSQL
def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Create cabinet table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS public.cabinet (
                    cabinet_id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    box_num INTEGER CHECK (box_num IN (1, 2, 3)),
                    taken BOOLEAN DEFAULT false,
                    medicine_bool BOOLEAN,
                    total_amount INTEGER,
                    breakfast INTEGER,
                    lunch INTEGER,
                    dinner INTEGER,
                    breakfast_status INTEGER,
                    lunch_status INTEGER,
                    dinner_status INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # # Pre-populate the cabinet table with three rows (for box 1, 2, and 3)
            # cursor.execute('''
            #     INSERT INTO public.cabinet (name, box_num, taken, medicine_bool, total_amount, breakfast, lunch, breakfast, breakfast_status, lunch_status, dinner_status)
            #     VALUES
            #     ('Box 1', 1, false, false, 0, 0, 0, 0, 'not taken', 'not taken', 'not taken'),
            #     ('Box 2', 2, false, false, 0, 0, 0, 0, 'not taken', 'not taken', 'not taken'),
            #     ('Box 3', 3, false, false, 0, 0, 0, 0, 'not taken', 'not taken', 'not taken')
            #     ON CONFLICT (box_num) DO NOTHING;
            # ''')

            conn.commit()


# Update a cabinet row (e.g., after medicine consumption or item update)
def update_cabinet(name, box_num, taken, medicine_bool, total_amount, breakfast, lunch, dinner, breakfast_status, lunch_status, dinner_status):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE public.cabinet
                SET name = %s,
                    taken = %s,
                    medicine_bool = %s,
                    total_amount = %s,
                    breakfast = %s,
                    lunch = %s,
                    dinner = %s,
                    breakfast_status = %s,
                    lunch_status = %s,
                    dinner_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE box_num = %s;
            ''', (name, taken, medicine_bool, total_amount, breakfast, lunch, breakfast, breakfast_status, lunch_status, dinner_status, box_num))

            conn.commit()

# Get cabinet details by box number
def get_cabinet_by_box_num(box_num):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.cabinet WHERE box_num = %s', (box_num,))
            return cursor.fetchone()
