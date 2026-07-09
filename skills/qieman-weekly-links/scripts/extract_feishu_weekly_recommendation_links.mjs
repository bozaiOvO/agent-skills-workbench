import fs from 'node:fs/promises';
import path from 'node:path';

function parseArgs(argv) {
  const parsed = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith('--')) continue;
    const body = arg.slice(2);
    if (body.includes('=')) {
      const [key, ...rest] = body.split('=');
      parsed.set(key, rest.join('=') || 'true');
      continue;
    }
    const next = argv[index + 1];
    if (next && !next.startsWith('--')) {
      parsed.set(body, next);
      index += 1;
    } else {
      parsed.set(body, 'true');
    }
  }
  return parsed;
}

const args = parseArgs(process.argv.slice(2));

function usage() {
  return `Usage:
  node extract_feishu_weekly_recommendation_links.mjs --weeklies weeklies.json --output-md out.md --output-json out.json
  node extract_feishu_weekly_recommendation_links.mjs --render-from-json result.json --output-md out.md

Options:
  --weeklies PATH           Weekly Feishu document list JSON.
  --output-md PATH          Markdown output path.
  --output-json PATH        Raw JSON output path.
  --render-from-json PATH   Regenerate Markdown from an existing raw JSON file without opening Feishu.
  --cdp-port PORT           Chrome DevTools Protocol port. Default: 9223.
  --domain HOST             Prefer a debuggable tab on this host. Default: cqnqd3fmrz9.feishu.cn.
  --max-pages N             Process at most N weekly pages after filtering.
  --max-items N             Process at most N catalogue entries per page.
  --from-vol N              Process volumes >= N.
  --to-vol N                Process volumes <= N.
  --volumes CSV             Process only specific volumes, e.g. 262,265,274.
  --page-delay-ms N         Wait after page navigation. Default: 2500.
  --click-delay-ms N        Wait after clicking a catalogue item. Default: 500.
  --max-wait-ms N           Wait for a target block after click. Default: 7000.
`;
}

if (args.has('help') || args.has('h')) {
  console.log(usage());
  process.exit(0);
}

const CDP_PORT = Number(args.get('cdp-port') || process.env.CDP_PORT || 9223);
const CDP_LIST_URL = `http://127.0.0.1:${CDP_PORT}/json/list`;
const TARGET_DOMAIN = args.get('domain') || process.env.FEISHU_DOMAIN || 'cqnqd3fmrz9.feishu.cn';
const WEEKLIES_PATH = args.get('weeklies') || process.env.QIEMAN_WEEKLIES_PATH || '/private/tmp/qieman_weeklies_2025_2026.json';
const OUTPUT_MD =
  args.get('output-md') ||
  process.env.QIEMAN_OUTPUT_MD ||
  path.resolve(process.cwd(), '且曼周刊推荐内容链接汇总.md');
const OUTPUT_JSON =
  args.get('output-json') ||
  process.env.QIEMAN_OUTPUT_JSON ||
  '/private/tmp/qieman_weekly_recommendation_links.json';
const PAGE_DELAY_MS = Number(args.get('page-delay-ms') || process.env.PAGE_DELAY_MS || 2500);
const CLICK_DELAY_MS = Number(args.get('click-delay-ms') || process.env.CLICK_DELAY_MS || 500);
const MAX_WAIT_MS = Number(args.get('max-wait-ms') || process.env.MAX_WAIT_MS || 7000);
const maxPages = args.has('max-pages') ? Number(args.get('max-pages')) : Infinity;
const maxItems = args.has('max-items') ? Number(args.get('max-items')) : Infinity;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function encodeJs(value) {
  return JSON.stringify(value);
}

function cleanText(value) {
  return String(value || '')
    .replace(/\u200b/g, '')
    .replace(/\u200c/g, '')
    .replace(/\u200d/g, '')
    .replace(/\ufeff/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function stripNumberPrefix(value) {
  return cleanText(value).replace(/^\d+[.．、]\s*/, '').trim();
}

function markdownEscape(value) {
  return cleanText(value)
    .replace(/\\/g, '\\\\')
    .replace(/\[/g, '\\[')
    .replace(/\]/g, '\\]')
    .replace(/\*/g, '\\*')
    .replace(/_/g, '\\_')
    .replace(/`/g, '\\`');
}

function unique(values) {
  return [...new Set(values.map(cleanText).filter(Boolean))];
}

function isPublicLink(url) {
  if (!url) return false;
  if (!/^https?:\/\//i.test(url)) return false;
  const lower = url.toLowerCase();
  if (lower.includes('feishu.cn')) return false;
  if (lower.includes('feishucdn.com')) return false;
  if (lower.includes('internal-api-')) return false;
  if (lower.includes('s3-imfile.')) return false;
  if (lower.includes('lf-package-cn.')) return false;
  return true;
}

function isVideoishLink(url) {
  const lower = String(url || '').toLowerCase();
  if (lower.includes('/search/')) return false;
  if (lower.includes('/hashtag/')) return false;
  return [
    'douyin.com',
    'iesdouyin.com',
    'bilibili.com',
    'youtube.com',
    'youtu.be',
    'xiaohongshu.com',
    'xhslink.com',
    'kuaishou.com',
    'ixigua.com',
    'weibo.com/tv',
    'v.qq.com',
  ].some((needle) => lower.includes(needle));
}

function volumeOf(weekly) {
  return Number((String(weekly?.title || '').match(/Vol\.(\d+)/) || [])[1]) || null;
}

function filterWeeklies(weeklies) {
  const fromVol = args.has('from-vol') ? Number(args.get('from-vol')) : null;
  const toVol = args.has('to-vol') ? Number(args.get('to-vol')) : null;
  const volumeSet = args.has('volumes')
    ? new Set(
        String(args.get('volumes'))
          .split(',')
          .map((value) => Number(value.trim()))
          .filter(Boolean),
      )
    : null;

  return weeklies.filter((weekly) => {
    const volume = volumeOf(weekly);
    if (volumeSet && !volumeSet.has(volume)) return false;
    if (fromVol !== null && volume < fromVol) return false;
    if (toVol !== null && volume > toVol) return false;
    return true;
  });
}

function pruneNoisyLinks(links) {
  const cleaned = unique(links);
  const hasDouyinVideo = cleaned.some((url) => /douyin\.com\/video\//i.test(url));
  if (!hasDouyinVideo) return cleaned;
  return cleaned.filter((url) => !/douyin\.com\/(search|hashtag)\//i.test(url));
}

class CdpClient {
  constructor(webSocketUrl) {
    this.webSocketUrl = webSocketUrl;
    this.nextId = 0;
    this.pending = new Map();
    this.ws = null;
  }

  async connect() {
    this.ws = new WebSocket(this.webSocketUrl);
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const pending = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
        else pending.resolve(message.result);
      }
    };
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
    await this.send('Page.enable');
    await this.send('Runtime.enable');
  }

  send(method, params = {}) {
    const id = ++this.nextId;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  async eval(expression, timeout = 60000) {
    const result = await this.send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
      timeout,
    });
    if (result.exceptionDetails) {
      throw new Error(JSON.stringify(result.exceptionDetails));
    }
    return result.result.value;
  }

  close() {
    this.ws?.close();
  }
}

async function connectToFeishuTab() {
  const tabs = await fetch(CDP_LIST_URL).then((response) => response.json());
  const page =
    tabs.find((tab) => tab.type === 'page' && tab.url.includes(TARGET_DOMAIN)) ||
    tabs.find((tab) => tab.type === 'page' && tab.url.includes('feishu.cn')) ||
    tabs.find((tab) => tab.type === 'page');
  if (!page?.webSocketDebuggerUrl) {
    throw new Error(`No debuggable Chrome page found on ${CDP_LIST_URL}`);
  }
  const client = new CdpClient(page.webSocketDebuggerUrl);
  await client.connect();
  return client;
}

async function waitFor(client, expression, timeoutMs = MAX_WAIT_MS) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = await client.eval(`(() => Boolean(${expression}))()`, 5000).catch(() => false);
    if (value) return true;
    await sleep(200);
  }
  return false;
}

async function navigateTo(client, url) {
  await client.send('Page.navigate', { url });
  await waitFor(
    client,
    `document.readyState === "complete" && location.href.includes(${encodeJs(new URL(url).pathname)})`,
    15000,
  );
  await sleep(PAGE_DELAY_MS);
  await waitFor(
    client,
    `document.querySelector(".catalogue__list-item") || document.body.innerText.includes("且曼内刊")`,
    15000,
  );
}

async function getCatalogue(client) {
  return client.eval(`(() => {
    const items = [...document.querySelectorAll('.catalogue__list-item')].map((li, index) => {
      const link = li.querySelector('a[href]');
      const text = (li.innerText || li.textContent || '').replace(/\\u200b/g, '').replace(/\\s+/g, ' ').trim();
      const className = String(li.className || '');
      const levelFromClass = (className.match(/heading-(\\d+)/) || [])[1];
      return {
        index,
        id: li.dataset.id || '',
        level: Number(li.dataset.sourceLevel || levelFromClass || 0),
        text,
        href: link ? link.href : '',
        className,
      };
    }).filter((item) => item.id && item.text);

    let section = '';
    const entries = [];
    for (const item of items) {
      const normalized = item.text.replace(/^#+\\s*/, '').trim();
      if (!/^\\d+[.．、]\\s*/.test(item.text) && item.level <= 2) {
        section = normalized;
      }
      if (/^\\d+[.．、]\\s*/.test(item.text)) {
        entries.push({ ...item, section });
      }
    }

    return {
      url: location.href.split('#')[0],
      title: document.title.replace(/[\\u200b\\u200c\\u200d\\ufeff]/g, ''),
      items,
      entries,
    };
  })()`);
}

async function clickCatalogueItem(client, id) {
  const clicked = await client.eval(`(() => {
    const id = ${encodeJs(id)};
    const selector = '.catalogue__list-item[data-id="' + CSS.escape(id) + '"] a[href]';
    const link = document.querySelector(selector) || document.querySelector('a[href="#' + CSS.escape(id) + '"]');
    if (!link) return false;
    link.click();
    return true;
  })()`);
  if (!clicked) return false;

  const found = await waitFor(client, `document.querySelector('[data-record-id="${id}"]')`, MAX_WAIT_MS);
  if (!found) await sleep(CLICK_DELAY_MS);
  else await sleep(CLICK_DELAY_MS);
  return found;
}

async function extractCurrentItem(client, id) {
  return client.eval(`(() => {
    const targetId = ${encodeJs(id)};
    const externalUrlRe = /https?:\\\/\\\/[^\\s"'<>，。；）)\\]】]+/g;

    function clean(value) {
      return String(value || '')
        .replace(/[\\u200b\\u200c\\u200d\\ufeff]/g, '')
        .replace(/\\s+/g, ' ')
        .trim();
    }

    function normalizeUrl(url) {
      if (!url) return '';
      let value = String(url).trim();
      try { value = decodeURIComponent(value); } catch (error) {}
      value = value.replace(/[\\u200b\\u200c\\u200d\\ufeff]/g, '');
      value = value.replace(/^http\\s*:\\s*\\/\\//i, 'https://');
      value = value.replace(/^https\\s*:\\s*\\/\\//i, 'https://');
      value = value.replace(/[，。；、)）\\]】]+$/g, '');
      return value;
    }

    function collectLinks(block) {
      const links = [];
      for (const link of block.querySelectorAll('a[href], [data-href], [data-url], [auto-url]')) {
        const href =
          link.getAttribute('href') ||
          link.getAttribute('data-href') ||
          link.getAttribute('data-url') ||
          link.getAttribute('auto-url') ||
          '';
        const normalized = normalizeUrl(href);
        if (normalized) {
          links.push({
            url: normalized,
            text: clean(link.innerText || link.textContent || ''),
            source: link.tagName.toLowerCase(),
          });
        }
      }

      for (const media of block.querySelectorAll('video[src], iframe[src]')) {
        const src = normalizeUrl(media.getAttribute('src') || '');
        if (src) links.push({ url: src, text: clean(media.getAttribute('title') || ''), source: media.tagName.toLowerCase() });
      }

      const text = block.innerText || block.textContent || '';
      const patched = text.replace(/https?\\s*:\\s*\\/\\//gi, (match) => match.replace(/\\s+/g, ''));
      for (const match of patched.matchAll(externalUrlRe)) {
        const normalized = normalizeUrl(match[0]);
        if (normalized) links.push({ url: normalized, text: normalized, source: 'text' });
      }
      return links;
    }

    function blockInfo(block) {
      const rect = block.getBoundingClientRect();
      return {
        type: block.getAttribute('data-block-type') || '',
        blockId: block.getAttribute('data-block-id') || '',
        recordId: block.getAttribute('data-record-id') || '',
        text: clean(block.innerText || block.textContent || ''),
        links: collectLinks(block),
        rect: { top: rect.top, bottom: rect.bottom },
      };
    }

    const target = document.querySelector('[data-record-id="' + CSS.escape(targetId) + '"]');
    if (!target) {
      return {
        found: false,
        visibleRecordIds: [...document.querySelectorAll('.block[data-record-id]')]
          .map((block) => block.getAttribute('data-record-id'))
          .filter(Boolean),
      };
    }

    const blocks = [...document.querySelectorAll('.block[data-record-id]')];
    const startIndex = blocks.indexOf(target);
    const group = [];
    for (let index = startIndex; index < blocks.length && group.length < 30; index += 1) {
      const block = blocks[index];
      const type = block.getAttribute('data-block-type') || '';
      if (index > startIndex && /^heading[123]$/.test(type)) break;
      group.push(blockInfo(block));
    }

    const directBlocks = group.filter((block, index) => {
      if (index === 0) return true;
      return ['text', 'quote', 'ordered', 'bullet', 'todo', 'heading3'].includes(block.type);
    });
    const preferredLinks = directBlocks.flatMap((block) => block.links);
    const allLinks = preferredLinks.length > 0 ? preferredLinks : group.flatMap((block) => block.links);
    const uniqueLinks = [];
    const seen = new Set();
    for (const link of allLinks) {
      if (!link.url || seen.has(link.url)) continue;
      seen.add(link.url);
      uniqueLinks.push(link);
    }

    return {
      found: true,
      target: blockInfo(target),
      group,
      links: uniqueLinks,
      scrollTop: document.querySelector('.bear-web-x-container')?.scrollTop ?? null,
    };
  })()`);
}

function publicLinksFrom(links) {
  return pruneNoisyLinks(links.map((link) => link.url).filter(isPublicLink));
}

function internalMediaLinksFrom(links) {
  return unique(
    links
      .map((link) => link.url)
      .filter((url) => /^https?:\/\//i.test(url))
      .filter((url) => !isPublicLink(url)),
  );
}

function renderMarkdown(results, missingVolumes) {
  const generatedAt = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
  const totalEntries = results.reduce((sum, page) => sum + page.entries.length, 0);
  const totalWithPublicLinks = results.reduce(
    (sum, page) => sum + page.entries.filter((entry) => entry.publicLinks.length > 0).length,
    0,
  );
  const totalVideoish = results.reduce(
    (sum, page) => sum + page.entries.filter((entry) => entry.publicLinks.some(isVideoishLink)).length,
    0,
  );
  const emptyPages = results.filter((page) => !page.error && page.entries.length === 0);
  const failedEntries = results.flatMap((page) =>
    page.entries
      .filter((entry) => !entry.found)
      .map((entry) => `${page.weekly.title} / ${entry.originalText}`),
  );

  const lines = [];
  lines.push('# 且曼周刊推荐内容链接汇总');
  lines.push('');
  lines.push(`生成时间：${generatedAt}`);
  lines.push('');
  lines.push(`范围：2025-2026 且曼周刊，已读取 ${results.length} 篇。`);
  lines.push(`目录条目：${totalEntries} 条；发现公开外部链接：${totalWithPublicLinks} 条；其中视频/短视频域名链接：${totalVideoish} 条。`);
  if (missingVolumes.length > 0) {
    lines.push(`目录 API 中缺失 Vol.${missingVolumes.join('、Vol.')}，本文件未自行补齐。`);
  }
  if (emptyPages.length > 0 || failedEntries.length > 0) {
    const parts = [];
    if (emptyPages.length > 0) {
      parts.push(`空页：${emptyPages.map((page) => page.weekly.title).join('、')}`);
    }
    if (failedEntries.length > 0) {
      parts.push(`条目定位失败：${failedEntries.length} 条`);
    }
    lines.push(`核验说明：${parts.join('；')}。`);
  } else {
    lines.push('核验说明：已读取页面未出现空页或条目定位失败。');
  }
  lines.push('');
  lines.push('说明：优先记录条目下方的公开外部链接，例如抖音、B站、小红书、公众号、网页等；Markdown 不展示飞书定位链接，飞书定位和内部预览视频链接只在原始 JSON 中保留。');
  lines.push('');

  lines.push('## 视频/短视频链接索引');
  lines.push('');
  let videoCount = 0;
  for (const page of results) {
    const videoEntries = page.entries.filter((entry) => entry.publicLinks.some(isVideoishLink));
    if (videoEntries.length === 0) continue;
    lines.push(`### ${markdownEscape(page.weekly.title)}`);
    lines.push('');
    for (const entry of videoEntries) {
      videoCount += 1;
      const links = entry.publicLinks.filter(isVideoishLink);
      lines.push(`${videoCount}. ${markdownEscape(entry.section)} / ${markdownEscape(entry.title)}`);
      for (const link of links) {
        lines.push(`   - ${link}`);
      }
    }
    lines.push('');
  }
  if (videoCount === 0) lines.push('未发现视频/短视频域名链接。');
  lines.push('');

  lines.push('## 全部推荐条目');
  lines.push('');
  for (const page of results) {
    lines.push(`### ${markdownEscape(page.weekly.title)}`);
    lines.push('');
    lines.push(`源文档：${page.weekly.url}`);
    if (page.error) {
      lines.push('');
      lines.push(`读取失败：${markdownEscape(page.error)}`);
      lines.push('');
      continue;
    }

    let currentSection = '';
    for (const entry of page.entries) {
      if (entry.section !== currentSection) {
        currentSection = entry.section;
        lines.push('');
        lines.push(`#### ${markdownEscape(currentSection || '未命名分区')}`);
        lines.push('');
      }

      lines.push(`- ${markdownEscape(entry.originalText)}`);
      if (entry.publicLinks.length > 0) {
        for (const link of entry.publicLinks) {
          lines.push(`  - 链接：${link}`);
        }
      } else {
        lines.push('  - 链接：未在该条目正文块中发现公开外部链接');
      }
    }
    lines.push('');
  }

  return `${lines.join('\n')}\n`;
}

function missingVolumesFrom(weeklies) {
  const vols = weeklies
    .map(volumeOf)
    .filter(Boolean);
  if (vols.length === 0) return [];
  const present = new Set(vols);
  const missing = [];
  for (let vol = Math.min(...vols); vol <= Math.max(...vols); vol += 1) {
    if (!present.has(vol)) missing.push(vol);
  }
  return missing;
}

async function main() {
  if (args.has('render-from-json')) {
    const source = JSON.parse(await fs.readFile(args.get('render-from-json'), 'utf8'));
    await fs.mkdir(path.dirname(OUTPUT_MD), { recursive: true });
    await fs.writeFile(OUTPUT_MD, renderMarkdown(source.results || [], source.missingVolumes || []), 'utf8');
    console.log(`Wrote ${OUTPUT_MD}`);
    return;
  }

  const allWeeklies = JSON.parse(await fs.readFile(WEEKLIES_PATH, 'utf8'));
  const filteredWeeklies = filterWeeklies(allWeeklies);
  const weeklies = filteredWeeklies.slice(0, maxPages);
  const missingVolumes = missingVolumesFrom(allWeeklies);
  const client = await connectToFeishuTab();
  const results = [];

  try {
    for (const [pageIndex, weekly] of weeklies.entries()) {
      console.log(`[${pageIndex + 1}/${weeklies.length}] open ${weekly.title}`);
      const pageResult = { weekly, entries: [] };
      results.push(pageResult);

      try {
        await navigateTo(client, weekly.url);
        const catalogue = await getCatalogue(client);
        const entries = catalogue.entries.slice(0, maxItems);
        pageResult.catalogueCount = catalogue.items.length;
        pageResult.entryCount = entries.length;

        for (const [entryIndex, entry] of entries.entries()) {
          const section = cleanText(entry.section || '');
          const originalText = cleanText(entry.text);
          const title = stripNumberPrefix(originalText);
          const feishuAnchor = `${weekly.url}#${entry.id}`;

          process.stdout.write(`  - [${entryIndex + 1}/${entries.length}] ${section} / ${title.slice(0, 48)}... `);

          let extracted = { found: false, links: [] };
          try {
            const clicked = await clickCatalogueItem(client, entry.id);
            if (clicked) extracted = await extractCurrentItem(client, entry.id);
          } catch (error) {
            extracted = { found: false, error: String(error), links: [] };
          }

          const publicLinks = publicLinksFrom(extracted.links || []);
          const internalMediaLinks = internalMediaLinksFrom(extracted.links || []);
          pageResult.entries.push({
            section,
            originalText,
            title,
            id: entry.id,
            feishuAnchor,
            found: Boolean(extracted.found),
            publicLinks,
            internalMediaLinks,
            rawLinks: extracted.links || [],
            error: extracted.error || '',
          });

          console.log(`${publicLinks.length} public links`);
        }
      } catch (error) {
        pageResult.error = String(error);
        console.log(`  ! failed: ${pageResult.error}`);
      }
    }
  } finally {
    client.close();
  }

  await fs.mkdir(path.dirname(OUTPUT_MD), { recursive: true });
  await fs.writeFile(OUTPUT_JSON, JSON.stringify({ results, missingVolumes }, null, 2), 'utf8');
  await fs.writeFile(OUTPUT_MD, renderMarkdown(results, missingVolumes), 'utf8');
  console.log(`Wrote ${OUTPUT_MD}`);
  console.log(`Wrote ${OUTPUT_JSON}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
