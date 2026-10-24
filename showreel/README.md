# Claude — Motion Reel 2026

15-second motion graphics showreel, 1920×1080 @ 60 fps, with a synthesized soundtrack locked to 128 BPM (one scene per bar).

**Watch:** [`claude-showreel-2026.mp4`](claude-showreel-2026.mp4)

| Bar | Time | Scene |
|---|---|---|
| 0 | 0.00 s | Intro: dot → line → split reveal → iris wipe |
| 1 | 1.88 s | Form: point-morphing shapes, squash & stretch, echo trails, orbiters |
| 2 | 3.75 s | Type: slam, per-letter easing with a live curve, rhythm bounce, marquee wall |
| 3 | 5.63 s | Particles: 4,400 particles swirl into "FLOW", explode, warp out |
| 4 | 7.50 s | Dimension: isometric cube field with bounce drop-in and ripple |
| 5 | 9.38 s | Data: animated rings, bars, line chart, counter |
| 6 | 11.25 s | Montage: eight half-beat cuts with glitch hits, CRT power-off |
| 7 | 13.13 s | End card: CRT power-on, logo mark, name, credits |

## Rebuild

```sh
python3 soundtrack.py          # → soundtrack.wav
node render.js                 # → frames.mp4 (needs playwright + ffmpeg)
ffmpeg -i frames.mp4 -i soundtrack.wav -c:v libx264 -crf 21 -pix_fmt yuv420p \
       -c:a aac -b:a 256k -shortest -movflags +faststart claude-showreel-2026.mp4
```

Open `reel.html` in a browser for a live real-time preview (click to start audio).
Every frame is a pure function of time, so renders are exact and repeatable.
