import logging
import logging.config
import threading
from flask import Flask
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media, Media2, choose_mediaDB, db as clientDB
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, SECONDDB_URI
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime
import pytz

# Configure Logging
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

# "Spidey" Watermark in Logs
logging.info("══════════════════════════════════════")
logging.info("🔹 SpideyBot - Powered by Spidey 🔹")
logging.info(f"🔹 Pyrogram Version: {__version__} 🔹")
logging.info("══════════════════════════════════════")

# Flask Web Server for Health Checks
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "SpideyBot is running!"

def run_web():
    app_web.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web, daemon=True).start()

class SpideyBot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=10,
        )

    async def start(self):
        logging.info("🚀 SpideyBot is Starting...")
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        await super().start()
        await Media.ensure_indexes()
        await Media2.ensure_indexes()

        # Database Space Check
        stats = await clientDB.command('dbStats')
        free_dbSize = round(512 - ((stats['dataSize']/(1024*1024)) + (stats['indexSize']/(1024*1024))), 2)

        if SECONDDB_URI and free_dbSize < 10:
            logging.warning(f"⚠️ Low DB Space: {free_dbSize}MB left. Switching to Secondary DB.")
            tempDict["indexDB"] = SECONDDB_URI
        elif not SECONDDB_URI:
            logging.error("❌ SECONDDB_URI is Missing! Add it Now.")
            exit()
        else:
            logging.info(f"✅ DB Space: {free_dbSize}MB Available. Using Primary DB.")

        await choose_mediaDB()

        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username

        logging.info(f"🤖 {me.first_name} (Username: {me.username}) is Online.")
        logging.info(LOG_STR)
        logging.info(script.LOGO)

        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")

        await self.send_message(
            chat_id=LOG_CHANNEL,
            text=f"🚀 **SpideyBot Restarted**\n📅 Date: {today}\n🕒 Time: {time}"
        )

    async def stop(self, *args):
        await super().stop()
        logging.info("🛑 SpideyBot Stopped. Goodbye!")

    async def iter_messages(
        self, chat_id: Union[int, str], limit: int, offset: int = 0
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through chat messages sequentially."""
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1

# Start the Bot
app = SpideyBot()
app.run()
