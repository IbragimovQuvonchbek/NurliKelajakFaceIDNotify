import pyodbc
import time
import httpx
import asyncio
from datetime import datetime, date

# SQL Server connection info
SQL_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=hik;"
    "UID=sa;"
    "PWD=Quvonchbek2006@"
)

API_BASE = "http://127.0.0.1:8000/api/v1"
TELEGRAM_BOT_TOKEN = "8061178459:AAFffd5n0Vd_NQIxz8dAdD2SbGEA-H9dxGQ"

# Track already sent messages per day
sent_kirish = set()
sent_chiqish = set()
last_chiqish_sent_date = None
current_date = date.today()


# Get today's entries from database
def get_today_entries():
    conn = pyodbc.connect(SQL_CONNECTION_STRING)
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute("""
        SELECT employeeID, personName, authDateTime, deviceName
        FROM imvs
        WHERE CAST(authDateTime AS DATE) = ?
        ORDER BY authDateTime ASC
    """, today)
    rows = cursor.fetchall()
    conn.close()
    return rows


# Send Telegram message
async def send_telegram_message(student_id, name, timestamp, direction):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/get-telegram-id/", params={"student_id": str(student_id)})
        if resp.status_code != 200:
            print(f"❌ Telegram ID topilmadi: {student_id}")
            return

        telegram_id = resp.json()["telegram_id"]
        direction = direction.lower()

        if "kirish" in direction:
            status = "maktabga kirdi"
        elif "chiqish" in direction:
            status = "maktabdan chiqdi"
        else:
            status = f"{direction.lower()} bo‘ldi"

        msg = (
            f"📢 Farzandingiz <b>{name}</b> "
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} da {status}."
        )

        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        await client.post(telegram_api, json={
            "chat_id": telegram_id,
            "text": msg,
            "parse_mode": "HTML"
        })
        print(f"✅ Telegram ID topildi: {student_id}")

# Process entries: send first kirish, last chiqish at 17:20
async def process_entries():
    global last_chiqish_sent_date, current_date, sent_kirish, sent_chiqish

    # Reset tracking at midnight
    if date.today() != current_date:
        current_date = date.today()
        sent_kirish.clear()
        sent_chiqish.clear()
        last_chiqish_sent_date = None

    rows = get_today_entries()
    chiqish_latest = {}

    for row in rows:
        emp_id = str(int(row.employeeID))
        direction = row.deviceName.lower()

        # First kirish
        if "kirish" in direction and emp_id not in sent_kirish:
            sent_kirish.add(emp_id)
            await send_telegram_message(emp_id, row.personName, row.authDateTime, row.deviceName)

        # Always store latest chiqish for each student
        if "chiqish" in direction:
            chiqish_latest[emp_id] = row

    # Send chiqish messages once between 17:20–17:24
    now = datetime.now()
    today = now.date()
    if (
            now.hour == 17 and 40 <= now.minute < 45 and
            last_chiqish_sent_date != today
    ):
        for emp_id, row in chiqish_latest.items():
            if emp_id not in sent_chiqish:
                sent_chiqish.add(emp_id)
                await send_telegram_message(emp_id, row.personName, row.authDateTime, row.deviceName)

        last_chiqish_sent_date = today


# Main loop
async def main():
    while True:
        await process_entries()
        await asyncio.sleep(60)  # check every minute


if __name__ == "__main__":
    asyncio.run(main())
