const fs = require('fs');
const puppeteer = require('puppeteer-core');

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium-browser',
  '/usr/bin/chromium',
].filter(Boolean);

function findChrome() {
  for (const p of CHROME_CANDIDATES) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

const FOOTER_TEMPLATE = `
  <div style="width:100%; font-family:'Inter',sans-serif; font-size:8.5px; color:#8b93ac; padding:0 14mm; display:flex; justify-content:space-between;">
    <span></span>
    <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
  </div>
`;

/** Render a report URL to an A4 PDF buffer with page numbers and a thin page frame (drawn via @page/.print-frame CSS, which repeats per page since it's position:fixed and print media is used by default in page.pdf()). */
async function renderReportToPdf(url) {
  const executablePath = findChrome();
  if (!executablePath) {
    const err = new Error(
      'No local Chrome/Chromium install found for PDF export. Set CHROME_PATH to a Chrome executable.'
    );
    err.code = 'NO_CHROME';
    throw err;
  }

  const browser = await puppeteer.launch({ executablePath, headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });
    // Print in the light theme — dark-theme text colors read as washed-out on the white PDF page.
    await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: '<span></span>',
      footerTemplate: FOOTER_TEMPLATE,
      margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
    });
    return pdf;
  } finally {
    await browser.close();
  }
}

module.exports = { renderReportToPdf };
