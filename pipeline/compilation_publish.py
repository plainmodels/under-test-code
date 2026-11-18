"""Publish files for a monthly compilation: description.txt, metadata.json, thumbnail.png (grid of episode thumbnails).

    python compilation_publish.py <comp_dir> <channel: earth|contour> <planned "Thu 7 Jan 2027, 20:30 IST"> <ep_dir> ...

Reads <comp_dir>/chapters.txt and compilation.mp4 (from compile.py) and each episode's publish/metadata.json + thumbnail.png.
"""
import base64, json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

STYLE = {
    "earth": {"name": "Earth Worked Out", "tag": "Earth Worked Out: real physics, run on screen.", "bg": "#f3ede2", "ink": "#22303a",
              "acc": "#d9572b", "font": "Lato", "cat": "Science & Technology",
              "how": "Every number comes from a simulation or analysis written for that episode; every animation is drawn by code from its output.",
              "hashtags": "#science #physics #earth"},
    "contour": {"name": "Contour Notes", "tag": "Contour Notes: why places are the way they are, drawn from the data.", "bg": "#14203a",
                "ink": "#f4ead2", "acc": "#e8c170", "font": "C059", "cat": "Education",
                "how": "Every number is computed from public map and census data for that episode; every map is drawn by code from the data.",
                "hashtags": "#geography #maps #data"},
}


def main(comp, ch, planned, eps):
    comp = pathlib.Path(comp); S = STYLE[ch]; eps = [pathlib.Path(e) for e in eps]
    metas = [json.loads((e / "publish/metadata.json").read_text()) for e in eps]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(comp / "compilation.mp4")]))
    mins = round(dur / 60)
    titles = [m["title"] for m in metas]
    lines = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    desc = f"""{len(eps)} {S['name']} episodes back to back, {mins} minutes. Each is also on the channel as its own video, with its sources, data and code in that video's description.

{lines}

Chapters
{(comp / 'chapters.txt').read_text().strip()}

How this was made
These are {S['name']} episodes {eps[0].name[2:].lstrip('0')} to {eps[-1].name[2:].lstrip('0')}, joined without their end cards (the last keeps its own). {S['how']} Narration uses a synthetic voice.

{S['tag']}

{S['hashtags']}"""
    assert len(desc) <= 5000 and "<" not in desc and ">" not in desc, len(desc)
    (comp / "description.txt").write_text(desc)
    title = {"earth": f"Tsunamis, hurricanes, hail, tornadoes, earthquakes and volcanoes, simulated ({mins} min)",
             "contour": f"{len(eps)} maps that explain where people live, drawn from the data ({mins} min)"}[ch]
    assert len(title) <= 100, title
    tags = sorted({t for m in metas for t in m.get("tags", [])[:3]})[:15]
    meta = {"title": title, "category": S["cat"], "language": "English", "tags": tags, "made_for_kids": False,
            "altered_content_disclosure": "No (animation is not realistic; synthetic narration is not a real person's voice)",
            "comments": "Allow all (founder, 2026-11-16)", "planned": planned, "compilation_of": [e.name for e in eps],
            "duration_min": round(dur / 60, 1), "visibility": "NOT UPLOADED"}
    (comp / "metadata.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    imgs = [base64.b64encode((e / "publish/thumbnail.png").read_bytes()).decode() for e in eps]
    head = {"earth": ["THE PHYSICS,", "SIMULATED"], "contour": [f"{len(eps)} MAPS,", "MEASURED"]}[ch]
    js = """async ([imgs, S, head, mins]) => {
      const W = 1280, H = 720, c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
      x.fillStyle = S.bg; x.fillRect(0, 0, W, H);
      const load = b => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'data:image/png;base64,' + b; });
      const im = await Promise.all(imgs.map(load));
      const tw = 296, th = 166, gap = 12, cols = 4, x0 = (W - cols * tw - (cols - 1) * gap) / 2, y0 = 300;
      im.slice(0, 8).forEach((i, k) => { const cx = x0 + (k % cols) * (tw + gap), cy = y0 + Math.floor(k / cols) * (th + gap);
        x.drawImage(i, cx, cy, tw, th); x.strokeStyle = S.acc; x.lineWidth = 2; x.strokeRect(cx, cy, tw, th); });
      const ff = S.font === 'C059' ? 'C059, serif' : 'Lato, sans-serif';
      x.font = '900 92px ' + ff; x.fillStyle = S.ink; x.fillText(head[0], x0, 130);
      const w0 = x.measureText(head[0] + ' ').width; x.fillStyle = S.acc; x.fillText(head[1], x0 + w0, 130);
      x.fillStyle = S.ink; x.font = '700 44px ' + ff; x.fillText(mins + ' minutes  ·  ' + S.name, x0, 220);
      const k8 = im.length; if (k8 < 8) { const cx = x0 + 3 * (tw + gap), cy = y0 + th + gap;
        x.fillStyle = S.acc; x.font = '800 40px ' + ff; x.fillText(k8 + ' episodes', cx + 30, cy + 95); }
      return c.toDataURL('image/png').split(',')[1]; }"""
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True); p = b.new_page(); p.set_content("<html><body></body></html>")
        (comp / "thumbnail.png").write_bytes(base64.b64decode(p.evaluate(js, [imgs, S, head, mins]))); b.close()
    print(comp.name, title, f"{len(desc)} chars")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
