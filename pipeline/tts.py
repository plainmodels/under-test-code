"""Stage 1: narration. Synthesise each beat locally with Kokoro (Apache-2.0) and write the timeline.

    python tts.py <storyboard.json> <build_dir>

Outputs <build_dir>/audio/<beat>.wav, <build_dir>/narration.wav and <build_dir>/timeline.json.
Beats whose text and voice are unchanged are reused from cache, so edits re-synthesise only what changed.
"""
import hashlib
import json
import pathlib
import sys
import time

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODELS = pathlib.Path(__file__).resolve().parent / "models"
LEAD_IN = 0.6      # silence before the first beat
TAIL = 1.5         # silence after the last beat


def main(storyboard_path: str, build_dir: str) -> None:
    sb = json.loads(pathlib.Path(storyboard_path).read_text())
    build = pathlib.Path(build_dir)
    audio = build / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    kokoro = None
    sr = 24000
    gap = float(sb.get("gap", 0.4))
    timeline, chunks, t = [], [np.zeros(int(LEAD_IN * sr), dtype=np.float32)], LEAD_IN
    started = time.time()

    for beat in sb["beats"]:
        say = beat.get("say") or beat["text"]
        key = hashlib.sha256(f"{sb['voice']}|{sb['speed']}|{sb['lang']}|{say}".encode()).hexdigest()[:16]
        wav = audio / f"{beat['id']}.wav"
        tag = audio / f"{beat['id']}.key"
        if wav.exists() and tag.exists() and tag.read_text() == key:
            samples, sr = sf.read(wav, dtype="float32")
        else:
            if kokoro is None:
                kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
            samples, sr = kokoro.create(say, voice=sb["voice"], speed=float(sb["speed"]), lang=sb["lang"])
            samples = np.asarray(samples, dtype=np.float32)
            sf.write(wav, samples, sr)
            tag.write_text(key)
        dur = len(samples) / sr
        bgap = float(beat.get("gap", gap))  # optional per-beat pause, e.g. to hold a short title card
        timeline.append({"id": beat["id"], "start": round(t, 3), "speech": round(dur, 3),
                         "dur": round(dur + bgap, 3)})
        chunks += [samples, np.zeros(int(bgap * sr), dtype=np.float32)]
        t += dur + bgap

    tail = float(sb.get("tail", TAIL))
    chunks.append(np.zeros(int(tail * sr), dtype=np.float32))
    total = t + tail
    sf.write(build / "narration.wav", np.concatenate(chunks), sr)
    (build / "timeline.json").write_text(json.dumps({"total": round(total, 3), "sr": sr, "beats": timeline}, indent=1))
    words = sum(len(b["text"].split()) for b in sb["beats"])
    print(f"beats={len(timeline)} words={words} total={total:.1f}s ({total/60:.2f} min) "
          f"synth_wall={time.time()-started:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
