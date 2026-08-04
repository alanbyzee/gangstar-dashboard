const { chromium } = require('/Users/alan/.workbuddy/binaries/node/workspace/node_modules/playwright-core');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true, args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.route('**/*firebase*', r => r.abort());
  await page.route('**/*.firebasedatabase.app/**', r => r.abort());
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR:' + e.message));

  const url = 'file:///Users/alan/WorkBuddy/2026-07-27-22-07-48/gangstar-ops-hub/Gangstar%E8%BF%90%E8%90%A5%E7%9C%8B%E6%9D%BF.html';
  await page.goto(url);
  await page.waitForTimeout(400);
  await page.evaluate(() => localStorage.removeItem('gangstar_custom'));
  await page.reload();
  await page.waitForTimeout(400);

  // --- Test 1: 一次性添加（点预设 + 自定义回车，不再多余点击）---
  await (await page.$('.sa-add-btn')).click();
  await page.waitForTimeout(250);
  const preset = await page.$('#ht-pool .ht-chip');
  const presetText = await preset.innerText();
  await preset.click();                 // 点一下预设 -> 加入已选
  await page.fill('#ht-custom', 'mytag1');
  await page.keyboard.press('Enter');   // 回车 -> 加入已选（不再需要再点）
  await page.waitForTimeout(150);
  const selCount = await page.evaluate(() => document.querySelectorAll('#ht-selected .ht-chip').length);
  console.log('已选数量(1预设+1自定义):', selCount, '(期望2)');
  await page.fill('#m-title', 'TEST_A');
  await page.click('.btn-save');
  await page.waitForTimeout(250);
  const saved1 = await page.evaluate(() => JSON.parse(localStorage.getItem('gangstar_custom')||'{}'));
  console.log('保存结果1:', JSON.stringify(saved1));

  // --- Test 2: 已选里点一下=移除 ---
  await (await page.$('.sa-add-btn')).click();
  await page.waitForTimeout(250);
  await page.fill('#ht-custom', 'delme');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(100);
  const beforeDel = await page.evaluate(() => document.querySelectorAll('#ht-selected .ht-chip').length);
  await page.evaluate(() => document.querySelector('#ht-selected .ht-chip').click()); // 点已选标签
  await page.waitForTimeout(100);
  const afterDel = await page.evaluate(() => document.querySelectorAll('#ht-selected .ht-chip').length);
  console.log('移除测试: 删除前', beforeDel, '删除后', afterDel, '(期望 1->0)');
  await page.evaluate(() => document.querySelector('.btn-cancel').click());

  // --- Test 3: × 移除 ---
  await (await page.$('.sa-add-btn')).click();
  await page.waitForTimeout(250);
  await page.fill('#ht-custom', 'xtag');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(100);
  await page.evaluate(() => document.querySelector('#ht-selected .ht-x').click());
  await page.waitForTimeout(100);
  const afterX = await page.evaluate(() => document.querySelectorAll('#ht-selected .ht-chip').length);
  console.log('×移除测试: 点击×后剩余', afterX, '(期望0)');
  await page.evaluate(() => document.querySelector('.btn-cancel').click());

  console.log('PAGE ERRORS:', errs.length ? errs.join(' | ') : 'none');
  await browser.close();
})();
