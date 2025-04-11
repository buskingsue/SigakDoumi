# db_sql.py

# Create the cabinet table with the required columns.


create_cabinet_table = """
CREATE TABLE public.cabinet (
    cabinet_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    box_num INTEGER CHECK (box_num IN (1, 2, 3)),
    taken BOOLEAN DEFAULT false,           -- New column indicating occupancy
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
"""

# Pre-populate the cabinet table with three rows (for box 1, 2, and 3).
insert_default_cabinet_rows = """
INSERT INTO public.cabinet (name, box_num, taken, medicine_bool, total_amount, breakfast, lunch, dinner, breakfast_status, lunch_status, dinner_status)
VALUES
('Box 1', 1, false, false, 0, 0, 0, 0, 0, 0, 0),
('Box 2', 2, false, false, 0, 0, 0, 0, 0, 0, 0),
('Box 3', 3, false, false, 0, 0, 0, 0, 0, 0, 0);
"""

# Query to select a cabinet row by box number.
select_cabinet_by_box = """
SELECT * FROM public.cabinet
WHERE box_num = %s;
"""

# Query to select a cabinet row by medicine name.
select_cabinet_by_medicine = """
SELECT box_num FROM public.cabinet
WHERE name = %s;
"""

# Query to update a cabinet row (e.g., after medicine consumption or item update).
update_cabinet = """
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
"""

# Query to delete or clear the contents of a cabinet row (if needed).
remove_cabinet_contents = """
UPDATE public.cabinet
SET name = NULL,
    taken = false,
    medicine_bool = false,
    total_amount = 0,
    breakfast = 0,
    lunch = 0,
    dinner = 0,
    breakfast_status = 0,
    lunch_status = 0,
    dinner_status = 0,
    updated_at = CURRENT_TIMESTAMP
WHERE box_num = %s;
"""

select_empty_cabinet = """
SELECT box_num FROM public.cabinet
WHERE taken = false
ORDER BY box_num ASC
LIMIT 1;
"""