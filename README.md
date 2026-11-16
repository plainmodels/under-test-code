# Under Test: the code behind the videos

Computer mysteries, measured on one laptop. YouTube: @UnderTestLab

Every number said in a video comes from code in this repository. Each episode has:

- `experiments/<episode>-<topic>/`: the original computation (simulation, measurement or analysis) and its results.
- `episodes/<episode>/`: `build_data.py` turns those results into `data.json`; `make_storyboard.py` writes the script,
  with every number pulled from `data.json`; `factcheck.csv` lists every claim with its source and status:
  VERIFIED (checked against the cited page), OBSERVED (computed here), BY CONSTRUCTION / STANDARD (a formula),
  ESTIMATED (derived, said as an estimate on screen) or UNKNOWN.
- `pipeline/`: how the video is made. Narration is synthesised locally with the Kokoro text-to-speech model (`tts.py`),
  every frame is drawn in code on an HTML canvas and captured with Playwright (`render.py`, `engine/engine.js`), then
  assembled with ffmpeg and checked against a Whisper transcription (`assemble.py`). No stock footage or generated images.

Paths in the scripts are relative to the original project folder; model weights and large raw data files are not included
(see each experiment for where its data comes from).

Code: MIT licence. Found a mistake? Open an issue: corrections are welcome and get noted in the video description.

Episodes are added here as each video goes public.
