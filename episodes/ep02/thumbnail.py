"""Draw the episode 2 thumbnail from the measured latencies: python ep02/thumbnail.py"""
import base64, json, pathlib
from playwright.sync_api import sync_playwright
ep = pathlib.Path(__file__).resolve().parent
lat = json.loads((ep / "data.json").read_text())["latA"]
JS = r"""
([lat]) => {
  const W = 1280, H = 720, c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
  x.fillStyle = '#0d1117'; x.fillRect(0, 0, W, H);
  const g = x.createRadialGradient(900, 300, 60, 900, 360, 760); g.addColorStop(0, 'rgba(255,107,107,0.20)'); g.addColorStop(1, 'rgba(13,17,23,0)');
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  // the real 400 latencies: a flat line at 41 ms, exaggerated vertically around the median
  const px = 60, pw = 1160, y41 = 470;
  x.strokeStyle = '#30363d'; x.lineWidth = 2; x.setLineDash([10, 10]); x.beginPath(); x.moveTo(px, 640); x.lineTo(px + pw, 640); x.stroke(); x.setLineDash([]);
  x.fillStyle = '#ff6b6b'; x.shadowColor = '#ff6b6b'; x.shadowBlur = 12;
  lat.forEach((v, i) => { const y = i === 0 ? 636 : y41 - (v - 41) * 60; x.beginPath(); x.arc(px + (i / 399) * pw, y, 5, 0, 7); x.fill(); });
  x.shadowBlur = 0; x.textBaseline = 'alphabetic';
  x.fillStyle = '#ffffff'; x.font = '800 96px "Noto Sans"'; x.fillText('WAITS', 56, 150);
  x.fillStyle = '#ff6b6b'; x.shadowColor = '#ff6b6b'; x.shadowBlur = 34; x.font = '800 230px "Noto Sans"'; x.fillText('40 ms', 46, 380); x.shadowBlur = 0;
  x.fillStyle = '#58a6ff'; x.font = '700 58px "Noto Sans"'; x.fillText('399 times out of 400.', 60, 590);
  x.fillStyle = '#8b949e'; x.font = '600 34px "Noto Sans Mono"'; x.fillText('0 ms', 60, 690); x.textAlign = 'right'; x.fillText('400 requests · same laptop', 1220, 690);
  return c.toDataURL('image/png').split(',')[1];
}"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", headless=True); p = b.new_page(); p.set_content("<html><body></body></html>")
    p.evaluate("Promise.all([document.fonts.load('800 100px \"Noto Sans\"'), document.fonts.load('600 40px \"Noto Sans Mono\"')])")
    out = ep / "publish" / "thumbnail.png"; out.write_bytes(base64.b64decode(p.evaluate(JS, [lat]))); b.close()
print("wrote", out)
