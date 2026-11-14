import os, json, hmac, hashlib, urllib.parse, asyncio
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from aiogram import Bot, Dispatcher
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "").strip()
APP_URL = os.getenv("APP_URL", "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
DB_PATH = os.getenv("DB_PATH", "centrala.db")
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
app = FastAPI(title="CENTRALA Telegram Mini App")
scheduler_task = None
ROOT = Path(__file__).parent

async def db():
    return await aiosqlite.connect(DB_PATH)

async def init_db():
    async with await db() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_grosz INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )""")
        await conn.commit()
        defaults = {
            "post_message": "Witamy! Zapraszamy do zapoznania się z aktualną ofertą CENTRALI.",
            "post_interval": "360",
        }
        for k, v in defaults.items():
            await conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))
        await conn.commit()

async def get_setting(key, default=""):
    async with await db() as conn:
        cur = await conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else default

async def set_setting(key, value):
    async with await db() as conn:
        await conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key,str(value)))
        await conn.commit()

def is_admin(user_id):
    return ADMIN_ID != 0 and user_id == ADMIN_ID

def money(grosz):
    return f"{grosz/100:.2f}".replace(".", ",") + " zł"

def verify_init_data(init_data: str):
    if not init_data:
        return None
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k,v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return None
        auth_date = int(parsed.get("auth_date", "0"))
        if abs(datetime.now(timezone.utc).timestamp() - auth_date) > 86400:
            return None
        user = json.loads(parsed.get("user", "{}"))
        return user if user.get("id") else None
    except Exception:
        return None

async def get_products():
    async with await db() as conn:
        cur = await conn.execute("SELECT id,name,price_grosz FROM products WHERE active=1 ORDER BY id")
        return [{"id":r[0], "name":r[1], "price":r[2]/100, "price_label":money(r[2])} for r in await cur.fetchall()]

@dp.message(Command("start"))
async def start_cmd(message):
    if not APP_URL:
        await message.answer("Aplikacja nie jest jeszcze skonfigurowana. Administrator musi ustawić APP_URL.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Otwórz CENTRALA", web_app=WebAppInfo(url=APP_URL))
    ]])
    await message.answer("Witaj w CENTRALI. Otwórz aplikację przyciskiem poniżej.", reply_markup=kb)

@dp.message(Command("pomoc"))
async def help_cmd(message):
    await message.answer(
        "<b>Komendy administratora</b>\n"
        "/addproduct nazwa | cena — dodaje produkt, np. /addproduct Produkt A | 60\n"
        "/products — lista produktów i ID\n"
        "/delproduct ID — wyłącza produkt\n"
        "/setmessage treść — ustawia automatyczny post\n"
        "/setinterval minuty — odstęp między postami (min. 60)\n"
        "/publish — publikuje wiadomość teraz\n"
        "/pomoc — ta instrukcja"
    )

@dp.message(Command("addproduct"))
async def add_product(message):
    if not is_admin(message.from_user.id): return
    raw = message.text.partition(" ")[2]
    try:
        name, price = [x.strip() for x in raw.split("|", 1)]
        price_float = float(price.replace(",", "."))
        if not name or price_float < 0: raise ValueError()
        cents = round(price_float * 100)
        async with await db() as conn:
            await conn.execute("INSERT INTO products(name,price_grosz) VALUES(?,?)", (name[:100], cents))
            await conn.commit()
        await message.answer(f"Dodano: <b>{name}</b> — {money(cents)}")
    except Exception:
        await message.answer("Format: /addproduct Nazwa produktu | 60")

@dp.message(Command("products"))
async def products_cmd(message):
    if not is_admin(message.from_user.id): return
    products = await get_products()
    if not products:
        await message.answer("Katalog jest pusty. Dodaj produkt: /addproduct Nazwa | 60")
        return
    await message.answer("\n".join(f"ID {p['id']}: {p['name']} — {p['price_label']}" for p in products))

@dp.message(Command("delproduct"))
async def del_product(message):
    if not is_admin(message.from_user.id): return
    try:
        pid = int(message.text.split(maxsplit=1)[1])
        async with await db() as conn:
            await conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
            await conn.commit()
        await message.answer("Produkt wyłączony z katalogu (jeśli takie ID istniało).")
    except Exception:
        await message.answer("Format: /delproduct ID")

@dp.message(Command("setmessage"))
async def set_post(message):
    if not is_admin(message.from_user.id): return
    body = message.text.partition(" ")[2].strip()
    if not body:
        await message.answer("Podaj treść: /setmessage Twoja wiadomość")
        return
    await set_setting("post_message", body[:3500])
    await message.answer("Zapisano treść automatycznej wiadomości.")

@dp.message(Command("setinterval"))
async def set_interval(message):
    if not is_admin(message.from_user.id): return
    try:
        minutes = int(message.text.split(maxsplit=1)[1])
        if minutes < 60 or minutes > 10080: raise ValueError()
        await set_setting("post_interval", str(minutes))
        await message.answer(f"Zapisano odstęp: {minutes} minut. Zmiana zacznie działać przy kolejnym cyklu.")
    except Exception:
        await message.answer("Podaj liczbę od 60 do 10080 minut. Np. /setinterval 360")

@dp.message(Command("publish"))
async def publish_now(message):
    if not is_admin(message.from_user.id): return
    if not GROUP_CHAT_ID:
        await message.answer("Brak GROUP_CHAT_ID w ustawieniach hostingu.")
        return
    try:
        await bot.send_message(GROUP_CHAT_ID, await get_setting("post_message"))
        await message.answer("Wiadomość opublikowana.")
    except Exception as e:
        await message.answer(f"Nie udało się opublikować. Sprawdź, czy bot jest administratorem grupy i czy GROUP_CHAT_ID jest poprawne. Szczegół: {str(e)[:250]}")

async def post_scheduler():
    last_post = 0
    while True:
        try:
            interval = max(60, int(await get_setting("post_interval", "360"))) * 60
            now = asyncio.get_running_loop().time()
            if GROUP_CHAT_ID and now - last_post >= interval:
                await bot.send_message(GROUP_CHAT_ID, await get_setting("post_message"))
                last_post = now
        except Exception as e:
            print("Scheduler error:", repr(e))
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup():
    global scheduler_task
    await init_db()
    if APP_URL and WEBHOOK_SECRET:
        await bot.set_webhook(
            url=f"{APP_URL}/telegram/webhook",
            secret_token=WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types()
        )
    scheduler_task = asyncio.create_task(post_scheduler())

@app.on_event("shutdown")
async def shutdown():
    if scheduler_task:
        scheduler_task.cancel()
    await bot.session.close()

@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/catalog")
async def catalog():
    return {"products": await get_products()}

@app.post("/api/order")
async def create_order(request: Request):
    data = await request.json()
    user = verify_init_data(request.headers.get("X-Telegram-Init-Data", ""))
    if not user:
        raise HTTPException(401, "Otwórz aplikację z poziomu Telegrama.")
    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity"))
        if quantity < 1 or quantity > 99: raise ValueError()
    except Exception:
        raise HTTPException(400, "Nieprawidłowa ilość lub produkt.")
    async with await db() as conn:
        cur = await conn.execute("SELECT name,price_grosz FROM products WHERE id=? AND active=1", (product_id,))
        product = await cur.fetchone()
    if not product:
        raise HTTPException(400, "Produkt jest już niedostępny.")
    name, price_cents = product
    region = str(data.get("region",""))[:100]
    city = str(data.get("city",""))[:100]
    service = str(data.get("service",""))[:100]
    contact = str(data.get("contact",""))[:150]
    note = str(data.get("note",""))[:1000]
    if not city or not service or not contact:
        raise HTTPException(400, "Uzupełnij miasto, usługę i kontakt.")
    total = price_cents * quantity
    uname = ("@" + user["username"]) if user.get("username") else "brak"
    msg = (
        "<b>NOWE ZGŁOSZENIE — CENTRALA</b>\n"
        f"Produkt: {name}\nIlość: {quantity}\nCena jednostkowa: {money(price_cents)}\n"
        f"<b>Wartość orientacyjna: {money(total)}</b>\n"
        f"Województwo/region: {region or 'nie podano'}\nMiasto: {city}\nUsługa: {service}\n"
        f"Kontakt klienta: {contact}\nTelegram klienta: {uname}\n"
        f"ID Telegram: <code>{user['id']}</code>\nWiadomość: {note or 'brak'}"
    )
    if ADMIN_ID:
        await bot.send_message(ADMIN_ID, msg)
    return {"ok": True, "message": "Zgłoszenie wysłane. Administrator skontaktuje się z Tobą."}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if WEBHOOK_SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        raise HTTPException(403, "Forbidden")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})
