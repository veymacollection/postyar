import json, os, random, time
import urllib.parse, urllib.request

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}/"

def call(method, **params):
    body = {k: json.dumps(v) if isinstance(v, (list, dict)) else v
            for k, v in params.items()}
    data = urllib.parse.urlencode(body).encode()
    with urllib.request.urlopen(API + method, data=data, timeout=30) as r:
        return json.load(r)

def footer():
    with open("config.json", encoding="utf-8") as f:
        data = json.load(f)
    return random.choice(data["captions"]) + "\n\n" + data["contact"]

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
            key = msg.get("media_group_id") or msg["message_id"]
            targets[key] = msg  # آخرین پیام آلبوم می‌مونه
    for msg in targets.values():
        caption = ((msg.get("caption") or "") + "\n\n" + footer()).strip()
        print(call("editMessageCaption", chat_id=msg["chat"]["id"],
                   message_id=msg["message_id"], caption=caption))
    if offset:
        call("getUpdates", offset=offset, limit=1)

main()
