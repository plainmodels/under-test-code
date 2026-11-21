"""Read-only YouTube Analytics for the Project Zero channels (separate tokens; cannot change anything on the channels).

  python yt_analytics.py auth <channel>        one-time consent (prints a URL; pick the right channel, Allow)
  python yt_analytics.py report [days=28]      markdown report for all channels with a token, to stdout

Tokens: $PZ_ROOT/.secrets/analytics-<channel>.json. Scopes: yt-analytics.readonly + youtube.readonly.
"""
import datetime, json, os, pathlib, sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = pathlib.Path(os.environ.get("PZ_ROOT", "."))
SECRETS = ROOT / ".secrets"
CLIENT = pathlib.Path.home() / "Downloads/yt-comment-mcp/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtube.readonly"]
CHANNELS = {"undertest": "UCB6zIe3-QDAwPsak457gy6g", "earth": "UCPW7uJFfPq5u6H08L2aANhg", "contour": "UCIgyRf19EnKChpMsSnLmc5Q",
            "everylayer": "UC4q4DCN9UtZt9iE0NQ9Aeiw", "money": "UClRx2prBxPoO-NnnZw-ufSQ", "wherefell": "UCt1cRlzXrZ-1IwB6ajoxquQ"}
NAMES = {"undertest": "Under Test", "earth": "Earth Worked Out", "contour": "Contour Notes",
         "everylayer": "Every Layer", "money": "Money, Entirely", "wherefell": "Where They Fell"}


def tok(ch):
    return SECRETS / f"analytics-{ch}.json"


def creds(ch):
    c = Credentials.from_authorized_user_file(str(tok(ch)), SCOPES)
    if not c.valid:
        c.refresh(Request()); tok(ch).write_text(c.to_json())
    return c


def auth(ch):
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    c = flow.run_local_server(port=int(os.environ.get("AUTH_PORT", "8766")), open_browser=False, access_type="offline", prompt="consent",
                              authorization_prompt_message="AUTH_URL {url}", success_message="Done. You can close this tab.")
    got = build("youtube", "v3", credentials=c, cache_discovery=False).channels().list(part="id", mine=True).execute()["items"][0]["id"]
    if got != CHANNELS[ch]:
        sys.exit(f"WRONG CHANNEL: token is for {got}, expected {CHANNELS[ch]} ({NAMES[ch]}); not saved")
    SECRETS.mkdir(exist_ok=True, mode=0o700); tok(ch).write_text(c.to_json()); tok(ch).chmod(0o600)
    print("saved", tok(ch).name, "for", NAMES[ch])


def report(days=28):
    end = datetime.date.today(); start = end - datetime.timedelta(days=int(days))
    out = [f"# Project Zero analytics, {start} to {end}\n"]
    for ch in CHANNELS:
        if not tok(ch).exists():
            out.append(f"## {NAMES[ch]}\nno analytics token\n"); continue
        c = creds(ch)
        ya = build("youtubeAnalytics", "v2", credentials=c, cache_discovery=False)
        yt = build("youtube", "v3", credentials=c, cache_discovery=False)
        q = dict(ids="channel==MINE", startDate=str(start), endDate=str(end))
        tot = ya.reports().query(**q, metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,dislikes").execute()
        rows = ya.reports().query(**q, dimensions="video", sort="-views", maxResults=15,
                                  metrics="views,averageViewDuration,averageViewPercentage,likes,dislikes,subscribersGained").execute().get("rows", [])
        titles = {}
        if rows:
            for v in yt.videos().list(part="snippet,contentDetails", id=",".join(r[0] for r in rows)).execute()["items"]:
                titles[v["id"]] = (v["snippet"]["title"], v["contentDetails"]["duration"])
        t = (tot.get("rows") or [[0] * 6])[0]
        out.append(f"## {NAMES[ch]}\nviews {t[0]}, watch time {round(t[1] / 60, 1)} h, avg view {t[2]} s, subs +{t[3]}, likes {t[4]}, dislikes {t[5]}\n")
        if rows:
            out.append("| video | length | views | avg view | % viewed | likes/dislikes | subs |\n|---|---|---|---|---|---|---|")
            for r in rows:
                title, dur = titles.get(r[0], (r[0], ""))
                out.append(f"| {title[:60]} | {dur.replace('PT', '').lower()} | {r[1]} | {r[2]} s | {round(r[3], 1)}% | {r[4]}/{r[5]} | {r[6]} |")
            out.append("")
    print("\n".join(out))


if __name__ == "__main__":
    {"auth": auth, "report": report}[sys.argv[1]](*sys.argv[2:])
