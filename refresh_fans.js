// Gangstar 粉丝数自动刷新脚本
// 用本机真实 Chrome 引擎打开 4 平台公开主页，提取粉丝/订阅数，写回 fan_data.json
// 公开页读数即真实数（已与用户后台核对一致，IG 1695 / FB 42 / YTB 489 / X 23），无需登录态
// 用法: node refresh_fans.js          -> 只读取并打印，不写回
//       node refresh_fans.js --write -> 读取并更新 fan_data.json（含历史追加）
const { chromium } = require('playwright-core');
const fs = require('fs');
const os = require('os');

const HUB = '/Users/alan/WorkBuddy/2026-07-27-22-07-48/gangstar-ops-hub';
const DATA = HUB + '/fan_data.json';
const TMP_PROFILE = os.tmpdir() + '/gangstar_refresh_profile';
const WRITE = process.argv.includes('--write');

const PLATFORMS = {
  instagram: { url: 'https://www.instagram.com/gangstarmiragecityindia/', dataKey: 'instagram' },
  facebook:  { url: 'https://www.facebook.com/profile.php?id=61572148744773', dataKey: 'facebook' },
  youtube:   { url: 'https://www.youtube.com/channel/UCEPkKwjbk3ZJ5rz9nXyjpWw', dataKey: 'youtube' },
  x:         { url: 'https://x.com/GangstarMCIndia', dataKey: 'x' },
};

function extract(key, body) {
  let m;
  if (key === 'instagram') m = body.match(/([\d,]+)\s*粉丝/);
  else if (key === 'facebook') m = body.match(/([\d,]+)\s*(位粉丝|关注者|followers?)/i);
  else if (key === 'youtube') m = body.match(/([\d,]+)\s*位订阅者/);
  else if (key === 'x') m = body.match(/([\d,]+)\s*Followers/i);
  if (m) return parseInt(m[0].replace(/[^\d]/g, ''), 10);
  return null;
}

(async () => {
  let data = null;
  try { data = JSON.parse(fs.readFileSync(DATA, 'utf-8')); } catch (e) {}
  const today = new Date().toISOString().slice(0, 10);
  try { fs.rmSync(TMP_PROFILE, { recursive: true, force: true }); } catch (e) {}
  let context;
  try {
    context = await chromium.launchPersistentContext(TMP_PROFILE, {
      channel: 'chrome', headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    });
  } catch (e) {
    console.log(JSON.stringify({ fatal: 'LAUNCH_FAIL', err: String(e).slice(0, 400) }));
    process.exit(1);
  }
  const out = {};
  for (const [key, cfg] of Object.entries(PLATFORMS)) {
    try {
      const page = await context.newPage();
      await page.goto(cfg.url, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(3500);
      const body = await page.evaluate(() => document.body.innerText);
      const v = extract(key, body);
      out[key] = { value: v, raw: body.replace(/\s+/g, ' ').slice(0, 150) };
      if (WRITE && data && v != null && v > 0) {
        const p = data.platforms[cfg.dataKey];
        if (p) {
          p.value = v;
          const hist = p.history || (p.history = []);
          const last = hist[hist.length - 1];
          if (last && last.date === today) last.value = v;
          else hist.push({ date: today, value: v });
          console.log(`[update] ${key}: ${v}`);
        }
      } else if (WRITE && data && (v == null || v <= 0)) {
        const cur = data.platforms[cfg.dataKey].value;
        console.log(`[skip] ${key}: 未读到有效数值（可能登录墙），保留 ${cur}`);
      }
      await page.close();
    } catch (e) {
      out[key] = { error: String(e).slice(0, 150) };
    }
  }
  await context.close();
  if (WRITE && data) {
    data.updated_at = today;
    fs.writeFileSync(DATA, JSON.stringify(data, null, 2));
    console.log('WROTE updated_at=' + today);
  }
  console.log(JSON.stringify(out, null, 2));
})();
