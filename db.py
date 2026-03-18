import psycopg2
import streamlit as st
from psycopg2.extras import RealDictCursor


import psycopg2
import socket
import streamlit as st
from psycopg2.extras import RealDictCursor


def get_connection():
    host = st.secrets["DB_HOST"]

    # 🔥 FORÇA IPv4 (corrige erro do Streamlit Cloud)
    try:
        ipv4 = socket.gethostbyname(host)
    except Exception:
        ipv4 = host  # fallback

    return psycopg2.connect(
        host=ipv4,
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=int(st.secrets.get("DB_PORT", 5432)),
        sslmode="require",
        cursor_factory=RealDictCursor,
    )


def execute(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def fetch(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def ensure_user(email, name, role="pilot_client", status="active"):
    query = """
    INSERT INTO users (email, name, role, status, last_login)
    VALUES (%s, %s, %s, %s, NOW())
    ON CONFLICT (email)
    DO UPDATE SET
        name = EXCLUDED.name,
        role = EXCLUDED.role,
        status = EXCLUDED.status,
        last_login = NOW()
    """
    execute(query, (email, name, role, status))


def log_usage(email, action, project):
    query = """
    INSERT INTO usage_logs (user_email, action_type, project_name, created_at)
    VALUES (%s, %s, %s, NOW())
    """
    execute(query, (email, action, project))
