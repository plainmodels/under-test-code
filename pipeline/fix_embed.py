"""Turn on embedding for scheduled/public videos whose API status says embeddable=false.

  python fix_embed.py <max_updates>

Fixes the soonest-to-publish videos first, across earth, contour and undertest. ~50 quota units per update,
so keep max_updates near 20 a day (the VPS comment agent shares the project's 10k daily quota).
Keeps privacyStatus, publishAt, license and made-for-kids exactly as they are.
"""
import sys, datetime
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import yt_api as Y

limit = int(sys.argv[1])
todo = []
for ch in ["earth", "contour", "undertest"]:
    Y.whoami(ch, quiet=True)
    s = Y.yt(ch)
    up = s.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = s.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    for i in range(0, len(ids), 50):
        for v in s.videos().list(part="status", id=",".join(ids[i:i + 50])).execute()["items"]:
            st = v["status"]
            if not st.get("embeddable"):
                todo.append((st.get("publishAt") or "0", ch, v["id"], st))
todo.sort()
print(datetime.datetime.now().isoformat(timespec="minutes"), "embed-off:", len(todo), "fixing:", min(limit, len(todo)))
for when, ch, vid, st in todo[:limit]:
    body = {k: st[k] for k in ("privacyStatus", "publishAt", "license", "selfDeclaredMadeForKids") if k in st}
    body["embeddable"] = True
    try:
        r = Y.yt(ch).videos().update(part="status", body={"id": vid, "status": body}).execute()
        print(" ", ch, vid, when, "embeddable", r["status"].get("embeddable"), "publishAt", r["status"].get("publishAt"))
    except Exception as e:
        print(" ", ch, vid, "FAILED", str(e)[:200])
        break
