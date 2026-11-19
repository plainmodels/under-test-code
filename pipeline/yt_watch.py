"""Watch a channel's uploads and apply our metadata to new Studio drafts (files uploaded in Studio keep their filename as title).

    python yt_watch.py <channel> <episode_base_dir> [minutes=180]

Draft title "cn09"            -> episode: title/description/tags/schedule/thumbnail (yt_api.meta)
Draft title "cn09 short1 x"   -> Short: title, description + full-video link, schedule (episode day + offset)
Draft title "cnc01 compilation" -> compilation in <base>/compilations/cnc01 (yt_api.compmeta)
Costs ~2 units a minute while idle, ~100 per episode, ~51 per Short. Each item is done once (records in publish/*.json).
"""
import datetime, json, pathlib, re, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import yt_api as Y

OFFSETS = {"earth": [2, 4, 6], "contour": [1, 4, 6], "undertest": [2, 4, 6]}


def short(api, ch, ep, sid, k, vid):
    recp = ep / "publish/shorts_upload.json"; recs = json.loads(recp.read_text()) if recp.exists() else {}
    if sid in recs: return False
    cfg = next(s for s in json.loads((ep / "shorts.json").read_text()) if s["id"] == sid)
    main = json.loads((ep / "publish/upload.json").read_text())["video_id"]
    when = Y.publish_at(json.loads((ep / "publish/metadata.json").read_text())["planned"]) + datetime.timedelta(days=OFFSETS[ch][k - 1])
    desc = cfg.get("description", "") + f"\n\nFull video: https://youtu.be/{main}\n\nNarration uses a synthetic voice."
    api.videos().update(part="snippet,status", body={"id": vid,
        "snippet": {"title": cfg["title"][:100], "description": desc, "categoryId": "27" if ch == "contour" else "28",
                    "defaultLanguage": "en", "defaultAudioLanguage": Y.LANG[ch]},
        "status": {"privacyStatus": "private", "publishAt": when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "selfDeclaredMadeForKids": False}}).execute()
    recs[sid] = {"video_id": vid, "publish_at_ist": when.isoformat()}; recp.write_text(json.dumps(recs, indent=1))
    print(ep.name, sid, vid, when.strftime("%a %d %b"), flush=True); return True


def main(ch, base, minutes=180):
    base = pathlib.Path(base); end = time.time() + 60 * float(minutes)
    while time.time() < end:
        try:
            api = Y.yt(ch)
            up = api.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            for it in api.playlistItems().list(part="snippet", playlistId=up, maxResults=50).execute()["items"]:
                t = re.sub(r"[\s_]+", "_", it["snippet"]["title"].strip()); vid = it["snippet"]["resourceId"]["videoId"]
                if m := re.fullmatch(r"([ec][cn]\d\d|ep\d\d)", t):
                    ep = base / m[1]
                    if ep.is_dir() and not (ep / "publish/upload.json").exists(): Y.meta(ch, str(ep), vid)
                elif m := re.fullmatch(r"([ec][cn]\d\d|ep\d\d)_(short(\d)_\w+)", t):
                    ep = base / m[1]
                    if (ep / "publish/upload.json").exists(): short(api, ch, ep, m[2], int(m[3]), vid)
                elif m := re.fullmatch(r"(\w+c\d\d)_compilation", t):
                    comp = base / "compilations" / m[1]
                    if comp.is_dir() and not (comp / "upload.json").exists(): Y.compmeta(ch, str(comp), vid)
        except SystemExit as e:
            print("ERR", e, flush=True)
        except Exception as e:
            print("ERR", str(e)[:200], flush=True)
        time.sleep(45)
    print("watch ended", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
