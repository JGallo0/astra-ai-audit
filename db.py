import psycopg2
import streamlit as st


def get_connection():
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=5432
    )
    return conn


def execute(query, params=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params)

    conn.commit()

    cur.close()
    conn.close()


def fetch(query, params=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, params)

    result = cur.fetchall()

    cur.close()
    conn.close()

    return result
  def ensure_user(email, name):

    query = """
    INSERT INTO users (email, name)
    VALUES (%s, %s)
    ON CONFLICT (email) DO NOTHING
    """

    execute(query, (email, name))
    def log_usage(email, action, project):

    query = """
    INSERT INTO usage_logs (user_email, action_type, project_name)
    VALUES (%s, %s, %s)
    """

    execute(query, (email, action, project))
    from db import ensure_user

ensure_user(user_email, user_name)
from db import log_usage

log_usage(user_email, "chat", project_name)
def execute(query, params=None):

    conn = get_connection()

    try:

        cur = conn.cursor()

        cur.execute(query, params)

        conn.commit()

    finally:

        cur.close()
        conn.close()
