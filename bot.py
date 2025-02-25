import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

# Spidey in Logs
logging.info("══════════════════════════════════════")
logging.info("🔹 SpideyBot - Powered by Spidey 🔹")
logging.info("══════════════════════════════════════")

from pyrogram import Client, __version__  # Spidey 
from pyrogram.raw.all import layer  # Spidey 
from database.ia_filterdb import Media, Media2, choose_mediaDB, db as clientDB  # Spidey Watermark
from database.users_chats_db import db  # Spidey 
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, SECONDDB_URI  # Spidey Watermark
from utils import temp  # Spidey 
from typing import Union, Optional, AsyncGenerator  # Spidey 
from pyrogram import types  # Spidey 
from Script import script  # Spidey 
from datetime import date, datetime  # Spidey 
import pytz  # Spidey 
from sample_info import tempDict  # Spidey 

class Bot(Client):

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
        logging.info("🚀 SpideyBot is Starting...")  # Spidey Watermark
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        await Media2.ensure_indexes()

        # Choose the right DB by checking the free space
        stats = await clientDB.command('dbStats')
        free_dbSize = round(512 - ((stats['dataSize']/(1024*1024)) + (stats['indexSize']/(1024*1024))), 2)

        if SECONDDB_URI and free_dbSize < 10:
            logging.info(f"⚠️ SpideyBot: Low DB Space: {free_dbSize}MB left. Switching to Secondary DB.")  # Spidey Watermark
            tempDict["indexDB"] = SECONDDB_URI
        elif not SECONDDB_URI:
            logging.error("❌ SpideyBot: SECONDDB_URI is Missing! Add it Now.")  # Spidey Watermark
            exit()
        else:
            logging.info(f"✅ SpideyBot: DB Space: {free_dbSize}MB Available. Using Primary DB.")  # Spidey Watermark

        await choose_mediaDB()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username

        logging.info(f"🤖 SpideyBot {me.first_name} (Username: {me.username}) is Online.")  # Spidey Watermark
        logging.info(LOG_STR)
        logging.info(script.LOGO)

        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")

        await self.send_message(
            chat_id=LOG_CHANNEL,
            text=script.RESTART_TXT.format(today, time))  # Spidey Watermark
        

    async def stop(self, *args):
        await super().stop()
        logging.info("🛑 SpideyBot Stopped. Goodbye!")  # Spidey Watermark

    async def iter_messages(
        self, chat_id: Union[int, str], limit: int, offset: int = 0
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially."""
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
app = Bot()
app.run()
