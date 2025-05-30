import sqlite3

conn = sqlite3.connect('resumes.db')
c = conn.cursor()

c.execute('''
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    filename TEXT,
    category TEXT,
    score TEXT,
    branch TEXT,
    skills TEXT,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

''')

conn.commit()
conn.close()
