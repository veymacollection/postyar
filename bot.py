import json, os, asyncio, random
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
groups = {}

def footer():
    with open("config.json", encoding="utf-8") as f:
        data = json.load(f)
    return random.choice(data["captions"]) + "\n\n" + data["contact"]

async def edit_last(msg):
    old = msg.caption or ""
    new = (old + "\n\n" + footer()).strip()
    await msg.edit_caption(caption=new)

async def on_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    gid = msg.media_group_id
    if not gid:
        await edit_last(msg)
        return
    groups[gid] = msg
    await asyncio.sleep(2)
    if groups.get(gid) is msg:
        del groups[gid]
        await edit_last(msg)

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(
    filters.ChatType.CHANNEL & (filters.PHOTO | filters.VIDEO), on_post))
app.run_polling(allowed_updates=["channel_post"])
