"""YouTube Data API helper for the Project Zero channels (one OAuth token per channel).

  python yt_api.py auth <channel>            one-time consent: prints a URL; pick the right channel, Allow
  python yt_api.py whoami <channel>          prints the channel the token belongs to
  python yt_api.py upload <channel> <ep_dir> uploads <ep>.mp4 as private, scheduled at metadata "planned",
                                             sets thumbnail and English captions; writes publish/upload.json
  python yt_api.py short <channel> <ep_dir> <short_id> <publish "YYYY-MM-DD HH:MM" IST>
  python yt_api.py status <channel> <video_id>

Channels: earth, contour, undertest. Expected channel ids are checked before every write, so a token for the
wrong channel can never upload. OAuth client: the existing Desktop client in ~/Downloads/yt-comment-mcp
(founder approved its use, 2026-11-17). Tokens: ~/project-zero/.secrets/token-<channel>.json (git-ignored).
The API cannot set comment moderation, ads or end screens: do those in Studio after upload.
"""
import datetime, json, pathlib, re, sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = pathlib.Path(".")
SECRETS = ROOT / ".secrets"
CLIENT = pathlib.Path.home() / "Downloads/yt-comment-mcp/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CHANNELS = {"earth": "UCPW7uJFfPq5u6H08L2aANhg", "contour": "UCIgyRf19EnKChpMsSnLmc5Q", "undertest": "UCB6zIe3-QDAwPsak457gy6g"}
LANG = {"earth": "en-US", "contour": "en-GB", "undertest": "en-US"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def token_path(ch):
    return SECRETS / f"token-{ch}.json"


def auth(ch):
    SECRETS.mkdir(exist_ok=True, mode=0o700)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    creds = flow.run_local_server(port=8765, open_browser=False, access_type="offline", prompt="consent",
                                  authorization_prompt_message="AUTH_URL {url}", success_message="Done. You can close this tab.")
    token_path(ch).write_text(creds.to_json())
    token_path(ch).chmod(0o600)
    print("saved", token_path(ch).name)
    whoami(ch)


def yt(ch):
    creds = Credentials.from_authorized_user_file(str(token_path(ch)), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        token_path(ch).write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def whoami(ch, quiet=False):
    r = yt(ch).channels().list(part="snippet", mine=True).execute()
    items = r.get("items", [])
    got = items[0]["id"] if items else None
    if not quiet:
        print("token channel:", got, items[0]["snippet"]["title"] if items else "-", "| expected", CHANNELS[ch])
    if got != CHANNELS[ch]:
        sys.exit(f"WRONG CHANNEL for '{ch}': token belongs to {got}. Re-run auth and pick the right channel.")


def publish_at(planned):
    m = re.search(r"(\d{1,2}) (\w{3}) (\d{4}), (\d{1,2}):(\d{2}) IST", planned)
    if not m:
        sys.exit(f"cannot read planned slot: {planned!r}")
    d = datetime.datetime.strptime(f"{m[1]} {m[2]} {m[3]} {m[4]}:{m[5]}", "%d %b %Y %H:%M").replace(tzinfo=IST)
    return d


def insert(ch, video, snippet, when):
    if when <= datetime.datetime.now(IST) + datetime.timedelta(minutes=15):
        sys.exit(f"publish time {when} is too close or past; refusing")
    body = {"snippet": snippet,
            "status": {"privacyStatus": "private", "publishAt": when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "selfDeclaredMadeForKids": False, "embeddable": True, "license": "youtube"}}
    req = yt(ch).videos().insert(part="snippet,status", body=body,
                                 media_body=MediaFileUpload(str(video), chunksize=16 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"  uploaded {int(st.progress() * 100)}%", flush=True)
    return resp["id"]


def upload(ch, ep_dir):
    whoami(ch)
    ep = pathlib.Path(ep_dir).resolve()
    out = ep / "publish/upload.json"
    if out.exists():
        sys.exit(f"already uploaded: {out.read_text()}")
    meta = json.loads((ep / "publish/metadata.json").read_text())
    desc = (ep / "publish/description.txt").read_text()
    when = publish_at(meta["planned"])
    snippet = {"title": meta["title"], "description": desc, "tags": meta.get("tags", []), "categoryId": "28",
               "defaultLanguage": "en", "defaultAudioLanguage": LANG[ch]}
    vid = insert(ch, ep / f"{ep.name}.mp4", snippet, when)
    print("video id", vid)
    rec = {"video_id": vid, "publish_at_ist": when.isoformat(), "uploaded_ist": datetime.datetime.now(IST).isoformat(timespec="seconds")}
    out.write_text(json.dumps(rec, indent=1))
    api = yt(ch)
    try:
        api.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(ep / "publish/thumbnail.png"))).execute()
        rec["thumbnail"] = "set"
    except Exception as e:
        rec["thumbnail"] = f"FAILED: {e}"
    srt = ep / f"{ep.name}.srt"
    try:
        api.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "en", "name": "English", "isDraft": False}},
                              media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream")).execute()
        rec["captions"] = "set"
    except Exception as e:
        rec["captions"] = f"FAILED: {e}"
    out.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))


def short(ch, ep_dir, sid, when_str):
    whoami(ch)
    ep = pathlib.Path(ep_dir).resolve()
    cfg = next(s for s in json.loads((ep / "shorts.json").read_text()) if s["id"] == sid)
    rec_path = ep / "publish/shorts_upload.json"
    recs = json.loads(rec_path.read_text()) if rec_path.exists() else {}
    if sid in recs:
        sys.exit(f"already uploaded: {recs[sid]}")
    when = datetime.datetime.strptime(when_str, "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    main = json.loads((ep / "publish/upload.json").read_text())["video_id"] if (ep / "publish/upload.json").exists() else None
    desc = cfg.get("description", "")
    if main:
        desc += f"\n\nFull video: https://youtu.be/{main}"
    desc += "\n\nNarration uses a synthetic voice."
    snippet = {"title": cfg["title"][:100], "description": desc, "categoryId": "28", "defaultLanguage": "en", "defaultAudioLanguage": LANG[ch]}
    vid = insert(ch, ep / "shorts" / f"{sid}.mp4", snippet, when)
    recs[sid] = {"video_id": vid, "publish_at_ist": when.isoformat()}
    rec_path.write_text(json.dumps(recs, indent=1))
    print(sid, vid, when.isoformat())


def meta(ch, ep_dir, vid):
    """For a video uploaded in Studio: set title, description, tags, category, language, schedule and thumbnail
    (about 100 units; no upload). Captions, disclosures, comments and end screen stay in Studio."""
    whoami(ch, quiet=True)
    ep = pathlib.Path(ep_dir).resolve()
    m = json.loads((ep / "publish/metadata.json").read_text())
    when = publish_at(m["planned"])
    if when <= datetime.datetime.now(IST) + datetime.timedelta(minutes=15):
        sys.exit(f"publish time {when} is too close or past; refusing")
    api = yt(ch)
    cur = api.videos().list(part="snippet,status", id=vid).execute()["items"]
    if not cur or cur[0]["snippet"]["channelId"] != CHANNELS[ch]:
        sys.exit(f"{vid} is not on channel {ch}")
    cat = {"Education": "27", "Science & Technology": "28"}.get(m.get("category"), "28" if ch != "contour" else "27")
    body = {"id": vid,
            "snippet": {"title": m["title"], "description": (ep / "publish/description.txt").read_text(), "tags": m.get("tags", []),
                        "categoryId": cat, "defaultLanguage": "en", "defaultAudioLanguage": LANG[ch]},
            "status": {"privacyStatus": "private", "publishAt": when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "selfDeclaredMadeForKids": False, "embeddable": True, "license": "youtube"}}
    api.videos().update(part="snippet,status", body=body).execute()
    rec = {"video_id": vid, "publish_at_ist": when.isoformat(), "uploaded_via": "Studio (founder picked files), metadata via API"}
    try:
        api.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(ep / "publish/thumbnail.png"))).execute()
        rec["thumbnail"] = "set"
    except Exception as e:
        rec["thumbnail"] = f"FAILED: {str(e)[:120]}"
    (ep / "publish/upload.json").write_text(json.dumps(rec, indent=1))
    print(ep.name, json.dumps(rec))


def compmeta(ch, comp_dir, vid):
    """Compilation uploaded in Studio: metadata.json/description.txt/thumbnail.png sit in comp_dir itself."""
    whoami(ch, quiet=True)
    comp = pathlib.Path(comp_dir).resolve()
    m = json.loads((comp / "metadata.json").read_text())
    when = publish_at(m["planned"])
    cat = {"Education": "27"}.get(m.get("category"), "28")
    api = yt(ch)
    api.videos().update(part="snippet,status", body={"id": vid,
        "snippet": {"title": m["title"], "description": (comp / "description.txt").read_text(), "tags": m.get("tags", []), "categoryId": cat,
                    "defaultLanguage": "en", "defaultAudioLanguage": LANG[ch]},
        "status": {"privacyStatus": "private", "publishAt": when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "selfDeclaredMadeForKids": False}}).execute()
    rec = {"video_id": vid, "publish_at_ist": when.isoformat()}
    try:
        api.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(comp / "thumbnail.png"))).execute(); rec["thumbnail"] = "set"
    except Exception as e:
        rec["thumbnail"] = f"FAILED: {str(e)[:120]}"
    (comp / "upload.json").write_text(json.dumps(rec, indent=1))
    print(comp.name, json.dumps(rec))


def thumb(ch, ep_dir):
    """Retry the custom thumbnail for an uploaded episode (after phone verification)."""
    ep = pathlib.Path(ep_dir).resolve(); rec = json.loads((ep / "publish/upload.json").read_text())
    yt(ch).thumbnails().set(videoId=rec["video_id"], media_body=MediaFileUpload(str(ep / "publish/thumbnail.png"))).execute()
    rec["thumbnail"] = "set"; (ep / "publish/upload.json").write_text(json.dumps(rec, indent=1)); print(ep.name, "thumbnail set")


def status(ch, vid):
    r = yt(ch).videos().list(part="status,processingDetails,snippet", id=vid).execute()
    print(json.dumps(r.get("items", [{}])[0].get("status", {}), indent=1))
    print(json.dumps(r.get("items", [{}])[0].get("processingDetails", {}), indent=1))


if __name__ == "__main__":
    cmd, ch, *rest = sys.argv[1:]
    if ch not in CHANNELS:
        sys.exit(f"unknown channel {ch}")
    {"auth": auth, "whoami": whoami, "upload": upload, "short": short, "meta": meta, "compmeta": compmeta, "thumb": thumb, "status": status}[cmd](ch, *rest)
