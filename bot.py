import json, os, random, time
import urllib.parse, urllib.request

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}/"
MAIN = "veyma_collection"  # کانال اصلی (با متن بالای config.json)
WAIT = 20  # ثانیه صبر برای کامل شدن آلبوم

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
        caps = [c for c in data["captions"] if "ویما" not in c]
    return random.choice(caps) + "\n\n" + cfg["contact"]

def is_media(m):
    return bool(m.get("photo") or m.get("video"))

def edit(msg):
    ft = footer(msg["chat"])
    if ft is None:
        print("skip: no config for",
              msg["chat"].get("username") or msg["chat"]["id"])
        return
    caption = ((msg.get("caption") or "") + "\n\n" + ft).strip()
    try:
        print(call("editMessageCaption", chat_id=msg["chat"]["id"],
                   message_id=msg["message_id"], caption=caption))
    except Exception as e:
        print("edit failed:", e)

def main():
    updates = call("getUpdates", allowed_updates=["channel_post"],
                   limit=100).get("result", [])
    now = time.time()

    # تازه‌ترین زمان هر آلبوم
    newest = {}
    for u in updates:
        m = u.get("channel_post")
        if m and m.get("media_group_id"):
            k = (m["chat"]["id"], m["media_group_id"])
            newest[k] = max(newest.get(k, 0), m["date"])

    offset = None
    singles, groups = [], {}
    for u in updates:
        m = u.get("channel_post")
        if m:
            gid = m.get("media_group_id")
            last = newest[(m["chat"]["id"], gid)] if gid else m["date"]
            if now - last < WAIT:
                break  # تازه‌ست، برای اجرای بعدی بمونه
        offset = u["update_id"] + 1
        if m and is_media(m):
            gid = m.get("media_group_id")
            if gid:
                groups.setdefault((m["chat"]["id"], gid), []).append(m)
            else:
                singles.append(m)

    for m in singles:
        edit(m)
    for ms in groups.values():
        ms.sort(key=lambda x: x["message_id"])
        with_cap = [x for x in ms if x.get("caption")]
        edit(with_cap[0] if with_cap else ms[0])

    if offset:
        call("getUpdates", offset=offset, limit=1)

main()
