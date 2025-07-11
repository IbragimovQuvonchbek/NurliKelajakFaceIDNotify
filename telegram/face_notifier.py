import pyodbc
import time
import httpx
import asyncio
import pandas as pd
from datetime import datetime, date
from pathlib import Path

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
EXCEL_SEND_IDS = [101927389, 5091336899]

# Track already sent messages per day
sent_kirish = set()
sent_chiqish = set()
kirish_log = {}
last_chiqish_sent_date = None
excel_sent_date = None
current_date = date.today()

# Excel save path
excel_folder = Path("kirish_logs")
excel_folder.mkdir(exist_ok=True)

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

# Send Excel to specified Telegram users
async def send_excel_file(excel_path):
    async with httpx.AsyncClient() as client:
        for chat_id in EXCEL_SEND_IDS:
            with open(excel_path, "rb") as file:
                files = {'document': (excel_path.name, file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'chat_id': chat_id}
                telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
                response = await client.post(telegram_api, data=data, files=files)
                print(f"📤 Excel sent to {chat_id} with status: {response.status_code}")

# Process entries
async def process_entries():
    global last_chiqish_sent_date, current_date, sent_kirish, sent_chiqish, kirish_log, excel_sent_date

    if date.today() != current_date:
        current_date = date.today()
        sent_kirish.clear()
        sent_chiqish.clear()
        kirish_log.clear()
        last_chiqish_sent_date = None
        excel_sent_date = None

    rows = get_today_entries()
    chiqish_latest = {}

    for row in rows:
        emp_id = str(int(row.employeeID))
        direction = row.deviceName.lower()

        if "kirish" in direction and emp_id not in sent_kirish:
            sent_kirish.add(emp_id)
            kirish_log[emp_id] = {
                "ID": emp_id,
                "Name": row.personName,
                "Entry Time": row.authDateTime.strftime('%Y-%m-%d %H:%M:%S')
            }
            await send_telegram_message(emp_id, row.personName, row.authDateTime, row.deviceName)

        if "chiqish" in direction:
            chiqish_latest[emp_id] = row

    now = datetime.now()
    today = now.date()

    # Send chiqish messages
    if (now.hour == 17 and 40 <= now.minute < 45 and last_chiqish_sent_date != today):
        for emp_id, row in chiqish_latest.items():
            if emp_id not in sent_chiqish:
                sent_chiqish.add(emp_id)
                await send_telegram_message(emp_id, row.personName, row.authDateTime, row.deviceName)
        last_chiqish_sent_date = today

    # Save and send Excel
    if now.hour == 10 and 0 <= now.minute < 5 and excel_sent_date != today and kirish_log:
        df = pd.DataFrame(kirish_log.values())
        file_name = f"{today.strftime('%Y-%m-%d')}.xlsx"
        file_path = excel_folder / file_name

        # Insert total count row at the top
        count_row = pd.DataFrame([{
            "ID": f"Total: {len(df)} students", "Name": "", "Entry Time": ""
        }])
        final_df = pd.concat([count_row, df], ignore_index=True)

        # Save to Excel
        final_df.to_excel(file_path, index=False)
        await send_excel_file(file_path)
        excel_sent_date = today


# Main loop
async def main():
    while True:
        await process_entries()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
