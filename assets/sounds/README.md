# Unwind — Sound Files

Place the following WAV files in this folder. All files must be **WAV format** (PCM,
mono or stereo, any sample rate — 22050 Hz mono is fine and keeps file sizes small).

| File | Role | Recommended length |
|---|---|---|
| `chime_5min.wav` | Soft pre-bedtime chime — played once at T-5 min | 1–3 s |
| `chime_bedtime.wav` | Gentle chime when bedtime arrives and ritual prompt appears | 1–3 s |
| `dock_waiting.wav` | Short tone played on loop every 15–30 s while waiting for phone to be docked | 1–2 s |
| `dock_confirmed.wav` | Confirmation tone when phone is placed on dock / session starts / session resumes | 0.5–2 s |
| `pickup.wav` | Brief alert tone when phone is picked up mid-session | 0.5–1 s |
| `complete.wav` | Calming completion chime at end of ritual | 2–5 s |
| `ambient.wav` | Continuous calming soundscape played throughout the ritual; fades out at session end | 10–60 min |

## Tips

- Use **mono 22050 Hz 16-bit** WAV for everything except `ambient.wav` to keep sizes small.
- `ambient.wav` can be stereo 44100 Hz for quality, but mono 22050 Hz is also fine on a USB speaker.
- Keep `ambient.wav` at least as long as your longest ritual duration (default 30 min = 1800 s).
  If the file ends before the session does, playback will simply stop early.
- **Normalize / amplify all files before dropping them here** — use Audacity (Effect → Normalize to -1 dB)
  or ffmpeg: `ffmpeg -i input.wav -af "loudnorm=I=-14:LRA=7:TP=-1" output.wav`
- Good free sources: freesound.org, pixabay.com/music, zapsplat.com

## ALSA device

All sounds go to `hw:3,0`. If your USB speaker shows up on a different card, run
`aplay -l` on the Pi and update `APLAY_DEVICE` in `backend/sound.py`.
