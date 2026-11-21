import json, os, random, time
import urllib.parse, urllib.request

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}/"
MAIN = "veyma_collection"  # کانال اصلی (با متن بالای config.json)

def call(method, **params):
    body = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
            for k, v in params.items()}
    data = urllib.parse.urlencode(body).encode()
    with urllib.request.urlopen(API + method, data=data, timeout=30) as r:
        return json.load(r)

def footer(chat):
    with open("config.json", encoding="utf-8") as f:
        data = json.load(f)
    uname = (chat.get("username") or "").lower()
    if uname == MAIN:
        cfg = data
    else:
        chans = data.get("channels", {})
        cfg = chans.get(uname) or chans.get(str(chat["id"]))
    if not cfg:
        return None
    caps = cfg.get("captions")
    if not caps:
        # اگه کانال کپشن جدا نداشت، از کپشن‌های اصلی استفاده می‌کنه
        # (بدون کپشن‌هایی که اسم «ویما» توشونه)
        caps = [c for c in data["captions"] if "ویما" not in c]
    return random.choice(caps) + "\n\n" + cfg["contact"]

def main():
    updates = call("getUpdates", allowed_updates=["channel_post"],
                   limit=100).get("result", [])
    now = time.time()
    offset = None
    targets = {}
    for u in updates:
        msg = u.get("channel_post")
        if msg and now - msg["date"] < 20:
            break  # تازه‌ست، برای اجرای بعدی بمونه
        offset = u["update_id"] + 1
        if msg and (msg.get("photo") or msg.get("video")):
            gid = msg.get("media_group_id") or msg["message_id"]
            key = (msg["chat"]["id"], gid)
            targets[key] = msg  # آخرین پیام آلبوم می‌مونه
    for msg in targets.values():
        ft = footer(msg["chat"])
        if ft is None:
            print("skip: no config for",
                  msg["chat"].get("username") or msg["chat"]["id"])
            continue
        caption = ((msg.get("caption") or "") + "\n\n" + ft).strip()
        try:
            print(call("editMessageCaption", chat_id=msg["chat"]["id"],
                       message_id=msg["message_id"], caption=caption))
        except Exception as e:
            print("edit failed:", e)
    if offset:
        call("getUpdates", offset=offset, limit=1)

main()
