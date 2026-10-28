const { chromium } = require('/home/julian/projects/final_lift/frontend/mobile/node_modules/playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + __dirname + '/ariadne.html');
  await p.evaluate(() => document.fonts.ready);
  const base = { format: 'A4', printBackground: true, preferCSSPageSize: true };
  await p.pdf({ ...base, path: __dirname + '/_plain.pdf' });
  await p.pdf({ ...base, path: __dirname + '/_footer.pdf', displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font:8px Arial,sans-serif;color:#7A868D;padding:0 19mm;display:flex;justify-content:space-between"><span>Ariadne · Designed by Julian Trude · Authored with Claude Opus 5.5</span><span class="pageNumber"></span></div>' });
  await b.close();
})();
