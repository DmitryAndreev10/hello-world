// Renders reel.html frame-by-frame in headless Chromium and pipes the frames to ffmpeg.
//   node render.js                 → frames.mp4 (video only, 1080p60)
//   node render.js --stills 1,2.5  → still_<t>.png for the given timestamps (seconds)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

(async () => {
  const stillsArg = process.argv.indexOf('--stills');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'reel.html') + '?render');
  await page.evaluate(() => window.READY);
  const grab = async f => {
    const url = await page.evaluate(f => { window.renderFrame(f); return document.getElementById('c').toDataURL('image/png'); }, f);
    return Buffer.from(url.split(',')[1], 'base64');
  };

  if (stillsArg > 0) {
    for (const s of process.argv[stillsArg + 1].split(',')) {
      fs.writeFileSync(path.join(__dirname, `still_${s}.png`), await grab(Math.round(parseFloat(s) * 60)));
    }
    await browser.close();
    return;
  }

  const total = await page.evaluate(() => window.TOTAL_FRAMES);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '60', '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    path.join(__dirname, 'frames.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = 0; f < total; f++) {
    const buf = await grab(f);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 60 === 0) console.log(`frame ${f}/${total}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('done');
})();
