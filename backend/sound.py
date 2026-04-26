"""
Audio feedback for Unwind.

On Raspberry Pi (Linux): uses aplay (ALSA) with stdin streaming for ambient.
On macOS (dev): uses afplay (built-in) with a temp file for ambient.
If neither player is found, all methods are silent no-ops.
"""

import asyncio
import io
import os
import random
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Optional

SOUNDS_DIR = Path(__file__).parent.parent / "assets" / "sounds"
APLAY_DEVICE = "hw:3,0"

_APLAY   = shutil.which("aplay")    # Linux / Pi
_AFPLAY  = shutil.which("afplay")   # macOS

AUDIO_AVAILABLE = bool(_APLAY or _AFPLAY)

if _APLAY:
    print("[sound] using aplay (ALSA)")
elif _AFPLAY:
    print("[sound] using afplay (macOS)")
else:
    print("[sound] no audio player found — audio disabled")

_FILES = {
    "chime_5min":     "reminder.wav",
    "chime_bedtime":  "reminder.wav",
    "dock_waiting":   "phone_undocked.wav",
    "dock_confirmed": "confirm.wav",
    "pickup":         "error.wav",
    "complete":       "session_complete.wav",
    "ambient":        "calming.wav",
}


# ── WAV helpers ───────────────────────────────────────────────────────────────

def _wav_header(params: wave._wave_params, n_frames: int) -> bytes:
    """Build a minimal 44-byte PCM WAV header for n_frames of audio."""
    n_ch, sw, fr = params.nchannels, params.sampwidth, params.framerate
    data_size = n_frames * n_ch * sw
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, n_ch, fr,
        fr * n_ch * sw, n_ch * sw, sw * 8,
        b"data", data_size,
    )


def _write_wav_from_offset(src: Path, offset_secs: float) -> Optional[str]:
    """
    Write a temp WAV file starting from offset_secs into src.
    Returns the temp file path (caller must delete it), or None on error.
    """
    try:
        with wave.open(str(src)) as wf:
            params = wf.getparams()
            start = min(int(offset_secs * wf.getframerate()), max(0, wf.getnframes() - 1))
            wf.setpos(start)
            data = wf.readframes(wf.getnframes() - start)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as out:
            out.setparams(params)
            out.writeframes(data)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(buf.getvalue())
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"[sound] temp WAV error: {e}")
        return None


# ── Streaming helpers (aplay / stdin only) ────────────────────────────────────

def _stream_file(proc: subprocess.Popen, path: Path, offset_secs: float) -> None:
    """Thread: stream WAV from offset_secs into proc.stdin (aplay on Pi)."""
    CHUNK = 4096
    try:
        with wave.open(str(path)) as wf:
            params = wf.getparams()
            start = min(int(offset_secs * wf.getframerate()), max(0, wf.getnframes() - 1))
            n_remaining = wf.getnframes() - start
            wf.setpos(start)
            proc.stdin.write(_wav_header(params, n_remaining))
            frames_written = 0
            while frames_written < n_remaining:
                if proc.poll() is not None:
                    return
                n = min(CHUNK, n_remaining - frames_written)
                data = wf.readframes(n)
                if not data:
                    break
                proc.stdin.write(data)
                frames_written += n
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    except Exception as e:
        print(f"[sound] stream error: {e}")


def _stream_fading(
    proc: subprocess.Popen,
    path: Path,
    offset_secs: float,
    fade_secs: float,
    on_done: Optional[callable] = None,
) -> None:
    """Thread: stream WAV from offset with linear volume fade to silence (aplay on Pi)."""
    import audioop
    CHUNK = 1024
    try:
        with wave.open(str(path)) as wf:
            params = wf.getparams()
            fr = wf.getframerate()
            sw = wf.getsampwidth()
            start = min(int(offset_secs * fr), max(0, wf.getnframes() - 1))
            n_fade = min(int(fade_secs * fr), wf.getnframes() - start)
            wf.setpos(start)
            proc.stdin.write(_wav_header(params, n_fade))
            frames_done = 0
            while frames_done < n_fade:
                if proc.poll() is not None:
                    return
                n = min(CHUNK, n_fade - frames_done)
                data = wf.readframes(n)
                if not data:
                    break
                factor = max(0.0, 1.0 - frames_done / n_fade)
                data = audioop.mul(data, sw, factor)
                proc.stdin.write(data)
                frames_done += n
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    except Exception as e:
        print(f"[sound] fade error: {e}")
    if on_done:
        try:
            on_done()
        except Exception:
            pass


# ── SoundManager ──────────────────────────────────────────────────────────────

class SoundManager:
    def __init__(self):
        self._dock_task: Optional[asyncio.Task] = None
        self._ambient_proc: Optional[subprocess.Popen] = None
        self._ambient_play_start: Optional[float] = None
        self._ambient_offset: float = 0.0
        self._ambient_tmp: Optional[str] = None   # macOS temp file path
        self._fade_proc: Optional[subprocess.Popen] = None
        self._oneshots: list[subprocess.Popen] = []

    # ── internal helpers ──────────────────────────────────────────────────────

    def _resolve(self, key: str) -> Optional[Path]:
        if not AUDIO_AVAILABLE:
            return None
        p = SOUNDS_DIR / _FILES[key]
        if not p.exists():
            print(f"[sound] missing: {p.name}")
            return None
        return p

    def _kill(self, proc: Optional[subprocess.Popen]) -> None:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()

    def _remove_tmp(self) -> None:
        if self._ambient_tmp:
            try:
                os.unlink(self._ambient_tmp)
            except OSError:
                pass
            self._ambient_tmp = None

    # ── one-shot sounds ───────────────────────────────────────────────────────

    def stop_all_oneshots(self) -> None:
        """Kill every currently-playing one-shot sound immediately."""
        active = [p for p in self._oneshots if p.poll() is None]
        for p in active:
            self._kill(p)
        self._oneshots = []

    def stop_all(self) -> None:
        """Stop everything — call on any state transition to a quiet screen."""
        self.stop_dock_loop()
        self.stop_all_oneshots()
        self.stop_ambient()

    def play_once(self, key: str) -> None:
        p = self._resolve(key)
        if p is None:
            return
        if _APLAY:
            cmd = [_APLAY, "-D", APLAY_DEVICE, str(p)]
        else:
            cmd = [_AFPLAY, str(p)]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Prune finished procs and track this one
        self._oneshots = [p for p in self._oneshots if p.poll() is None]
        self._oneshots.append(proc)

    # ── dock waiting loop ─────────────────────────────────────────────────────

    async def _dock_loop_worker(self) -> None:
        try:
            while True:
                self.play_once("dock_waiting")
                await asyncio.sleep(random.uniform(15.0, 30.0))
        except asyncio.CancelledError:
            pass

    def start_dock_loop(self) -> None:
        if self._dock_task and not self._dock_task.done():
            return
        self._dock_task = asyncio.create_task(self._dock_loop_worker())

    def stop_dock_loop(self) -> None:
        if self._dock_task and not self._dock_task.done():
            self._dock_task.cancel()
        self._dock_task = None
        self.stop_all_oneshots()

    # ── ambient soundscape ────────────────────────────────────────────────────

    def start_ambient(self) -> None:
        self._kill(self._ambient_proc)
        self._remove_tmp()
        self._ambient_offset = 0.0
        self._launch_ambient(0.0)

    def pause_ambient(self) -> None:
        if self._ambient_play_start is not None:
            self._ambient_offset += time.time() - self._ambient_play_start
        self._kill(self._ambient_proc)
        self._remove_tmp()
        self._ambient_proc = None
        self._ambient_play_start = None

    def resume_ambient(self) -> None:
        self._kill(self._ambient_proc)
        self._remove_tmp()
        self._ambient_proc = None
        self._launch_ambient(self._ambient_offset)

    def stop_ambient(self) -> None:
        self._kill(self._ambient_proc)
        self._kill(self._fade_proc)
        self._remove_tmp()
        self._ambient_proc = None
        self._fade_proc = None
        self._ambient_play_start = None
        self._ambient_offset = 0.0

    def fade_out_ambient(self, duration_secs: float = 10.0) -> None:
        if self._ambient_play_start is not None:
            self._ambient_offset += time.time() - self._ambient_play_start
        self._kill(self._ambient_proc)
        self._remove_tmp()
        self._ambient_proc = None
        self._ambient_play_start = None

        p = self._resolve("ambient")
        if p is None:
            self.play_once("complete")
            self._ambient_offset = 0.0
            return

        if _APLAY:
            # Pi: stream fading audio via stdin
            proc = subprocess.Popen(
                [_APLAY, "-D", APLAY_DEVICE],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._fade_proc = proc
            offset = self._ambient_offset
            self._ambient_offset = 0.0
            threading.Thread(
                target=_stream_fading,
                args=(proc, p, offset, duration_secs, lambda: self.play_once("complete")),
                daemon=True,
            ).start()
        else:
            # macOS: no fade — stop immediately and play complete chime
            self._ambient_offset = 0.0
            self.play_once("complete")

    def _launch_ambient(self, offset_secs: float) -> None:
        p = self._resolve("ambient")
        if p is None:
            return

        if _APLAY:
            # Pi: stream directly from offset via stdin pipe
            proc = subprocess.Popen(
                [_APLAY, "-D", APLAY_DEVICE],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._ambient_proc = proc
            self._ambient_play_start = time.time()
            threading.Thread(
                target=_stream_file, args=(proc, p, offset_secs), daemon=True
            ).start()
        else:
            # macOS: write offset-adjusted WAV to a temp file, play with afplay
            def _write_and_play():
                tmp_path = _write_wav_from_offset(p, offset_secs)
                if tmp_path is None:
                    return
                self._ambient_tmp = tmp_path
                proc = subprocess.Popen(
                    [_AFPLAY, tmp_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._ambient_proc = proc
                self._ambient_play_start = time.time()
                # Clean up temp file after playback finishes naturally
                proc.wait()
                if self._ambient_tmp == tmp_path:
                    self._remove_tmp()

            threading.Thread(target=_write_and_play, daemon=True).start()


sounds = SoundManager()
