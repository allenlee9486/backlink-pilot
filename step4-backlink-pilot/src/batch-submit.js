#!/usr/bin/env node

// batch-submit.js — Batch backlink submission with resume support
// v2: Natural comments, URL in website field only, site rotation, priority ordering

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { createSession, delay, humanType } from './browser.js';

const TIMEOUT_MS = 30000;
const MIN_DELAY = 5000;  // Reduced for testing: 5-15s between submissions
const MAX_DELAY = 15000;

// --- Natural comment templates ---
// URL goes in the website field, NOT in the comment body
const COMMENT_TEMPLATES = [
  "Thanks for sharing this! Really useful perspective.",
  "Bookmarked this for later. Great write-up.",
  "This is exactly what I was looking for, thanks!",
  "Appreciate the detailed breakdown here.",
  "Nice article! Learned something new today.",
  "Well written and informative. Thanks for putting this together.",
  "Solid content. Will definitely come back for more.",
  "This is super helpful, thanks for the effort!",
  "Great explanation. Clear and easy to follow.",
  "Really enjoyed reading this. Keep it up!",
  "Interesting take on this topic. Thanks for sharing.",
  "Quality content right here. Appreciate it.",
  "This answered a question I've had for a while. Thanks!",
  "Good stuff! Shared this with a friend who'd find it useful.",
  "Came across this while researching — glad I did. Very informative.",
  "Simple and well explained. Exactly what the internet needs more of.",
  "Love how you broke this down step by step.",
  "This is one of the better articles I've read on this topic.",
  "Practical and to the point. Thanks!",
  "Helpful resource. Added to my reading list.",
];

// Commenter personas (rotate to look natural)
const PERSONAS = [
  { name: "Alex Chen", email: "alexc.dev@outlook.com" },
  { name: "Jamie Liu", email: "jamie.liu.writes@gmail.com" },
  { name: "Morgan Lee", email: "morganlee.tech@outlook.com" },
  { name: "Sam Rivera", email: "sam.r.creates@gmail.com" },
  { name: "Taylor Kim", email: "taylork.web@outlook.com" },
];

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// Load resources — supports both flat array and { profiles, blog_comments } format
function loadResources() {
  if (!existsSync('resources/backlink-resources.json')) {
    console.error('❌ resources/backlink-resources.json not found.');
    console.error('   Copy the example file and add your target blogs:');
    console.error('   cp resources/backlink-resources.example.json resources/backlink-resources.json');
    process.exit(1);
  }
  if (!existsSync('resources/sites.json')) {
    console.error('❌ resources/sites.json not found.');
    console.error('   Create it with your product info. See resources/ for format.');
    process.exit(1);
  }

  const raw = JSON.parse(readFileSync('resources/backlink-resources.json', 'utf-8'));
  const sites = JSON.parse(readFileSync('resources/sites.json', 'utf-8'));

  let allResources;
  if (Array.isArray(raw)) {
    allResources = raw;
  } else {
    allResources = [
      ...(raw.profiles || []),
      ...(raw.blog_comments || [])
    ];
  }

  return { resources: allResources, sites: sites.sites };
}

// Priority: blog_comment with url_field > blog_comment without > profile
function prioritizeResources(resources) {
  const scored = resources.map(r => {
    let score = 0;
    if (r.type === 'blog_comment') score += 10;
    if (r.has_url_field || r.Has_URL_Field === 'Yes') score += 5;
    if (!(r.has_captcha || r.Has_Captcha === 'Yes')) score += 3;
    // Boost tech/game/education URLs
    const u = (r.url || r.URL || '').toLowerCase();
    if (u.match(/tech|code|dev|game|puzzle|maze|math|edu|learn|tool|software/)) score += 2;
    return { ...r, _score: score };
  });
  scored.sort((a, b) => b._score - a._score);
  return scored;
}

// Normalize resource keys (Excel uses Title Case, JSON uses snake_case)
function normalizeResource(r) {
  return {
    type: r.type || r.Type || 'unknown',
    url: r.url || r.URL || '',
    has_captcha: r.has_captcha === true || r['Has Captcha'] === 'Yes',
    has_url_field: r.has_url_field === true || r['Has URL Field'] === 'Yes',
    link_strategy: r.link_strategy || r['Link Strategy'] || 'unknown',
  };
}

function getLogPath() {
  const date = new Date().toISOString().split('T')[0];
  return `logs/submissions-${date}.json`;
}

function loadLog() {
  if (!existsSync('logs')) mkdirSync('logs', { recursive: true });
  const logPath = getLogPath();
  if (existsSync(logPath)) return JSON.parse(readFileSync(logPath, 'utf-8'));
  return { date: new Date().toISOString().split('T')[0], submissions: [] };
}

function saveLog(log) {
  writeFileSync(getLogPath(), JSON.stringify(log, null, 2), 'utf-8');
}

// Also check global submission history (don't re-submit to same URL ever)
function loadGlobalHistory() {
  const histPath = 'logs/global-history.json';
  if (existsSync(histPath)) return new Set(JSON.parse(readFileSync(histPath, 'utf-8')));
  return new Set();
}

function saveGlobalHistory(history) {
  writeFileSync('logs/global-history.json', JSON.stringify([...history], null, 2), 'utf-8');
}

function isSubmitted(log, globalHistory, url, siteUrl) {
  const key = `${siteUrl}|${url}`;
  return globalHistory.has(key) || 
         globalHistory.has(url) || // backward compatibility
         log.submissions.some(s => s.url === url && s.site_url === siteUrl);
}

// --- Blog comment submission (v2: natural comments, URL in website field) ---
async function submitBlogComment(page, resource, site) {
  const norm = normalizeResource(resource);
  await page.goto(norm.url, { waitUntil: 'domcontentloaded', timeout: TIMEOUT_MS });
  await delay(3000); // Wait for page to settle

  // --- Pre-flight: Scroll to bottom and top to trigger lazy-loaded forms ---
  await page.evaluate(async () => {
    const delay = (ms) => new Promise(r => setTimeout(r, ms));
    if (document.body) {
      // Step scroll to trigger various lazy load thresholds
      window.scrollTo(0, document.body.scrollHeight * 0.3);
      await delay(500);
      window.scrollTo(0, document.body.scrollHeight * 0.6);
      await delay(500);
      window.scrollTo(0, document.body.scrollHeight * 0.9);
      await delay(500);
      window.scrollTo(0, document.body.scrollHeight);
      await delay(800);
    }
  });
  await delay(2000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await delay(1000);

  // Extra check: if URL has a comment hash, force scroll to it first
  if (norm.url.includes('#comment-')) {
    const hash = norm.url.split('#')[1];
    try {
      await page.evaluate((id) => {
        const el = document.getElementById(id) || document.querySelector(`[name="${id}"]`) || document.querySelector(`[id*="${id}"]`);
        if (el) {
          el.scrollIntoView({ behavior: 'auto', block: 'center' });
          return true;
        }
        return false;
      }, hash);
      await delay(1500);
    } catch (e) {}
  }

  // --- Step 1: Find comment textarea (or button to reveal it) ---
  const commentSelectors = [
    'textarea[name="comment"]',
    'textarea#comment',
    '#respond textarea',
    '.comment-respond textarea',
    'textarea[name*="comment" i]',
    'textarea[id*="comment" i]',
    'textarea[placeholder*="comment" i]',
    'textarea[placeholder*="reply" i]',
    'textarea[placeholder*="leave a message" i]',
    'textarea[placeholder*="thoughts" i]',
    'textarea[name*="message" i]',
    'textarea[class*="comment" i]',
    'div[contenteditable="true"]', // Modern editors
    '#comment-editor iframe', // Blogger iframe (special case)
    'iframe[src*="comment"]', // Any comment iframe
    'textarea', // Fallback to any textarea
  ];

  const revealSelectors = [
    'button:has-text("Post a Comment")',
    'button:has-text("Leave a Reply")',
    'button:has-text("Add a Comment")',
    'button:has-text("Write a Comment")',
    'a:has-text("Leave a Comment")',
    'a:has-text("Write a Comment")',
    'a:has-text("Post a Comment")',
    'a:has-text("Add a Comment")',
    '#respond a',
    '.comment-reply-link',
    '.show-comments',
    '#show-comments-button',
    '.comment-form-trigger',
    'button.reply',
    'a.reply'
  ];

  let commentSelector = null;

  // --- Pre-scan: check if form is in an iframe ---
  const iframes = await page.$$('iframe');
  for (const frame of iframes) {
    try {
      const src = await frame.getAttribute('src') || '';
      if (src.includes('comment') || src.includes('disqus') || src.includes('facebook')) {
        console.log(`    ℹ️  Found comment iframe: ${src.substring(0, 50)}...`);
        // We might need to switch context here in a real playwright script, 
        // but for batch-submit we'll focus on finding visible elements first.
      }
    } catch (e) {}
  }

  // Try to find textarea first
  for (const sel of commentSelectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        const rect = JSON.parse(await page.evaluate((s) => {
          const e = document.querySelector(s);
          if (!e) return JSON.stringify({ w: 0, h: 0 });
          const r = e.getBoundingClientRect();
          return JSON.stringify({ w: r.width, h: r.height });
        }, sel));
        if (rect.w > 5 && rect.h > 5) {
          commentSelector = sel;
          break;
        }
      }
    } catch (e) { continue; }
  }

  // If not found, try to reveal it
  if (!commentSelector) {
    for (const sel of revealSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible()) {
          console.log(`    🔘 Clicking reveal button: ${sel}`);
          await btn.click();
          await delay(2000);
          // Try finding textarea again
          for (const ts of commentSelectors) {
            const el = await page.$(ts);
            if (el && await el.isVisible()) {
              commentSelector = ts;
              break;
            }
          }
          if (commentSelector) break;
        }
      } catch (e) { continue; }
    }
  }

  if (!commentSelector) throw new Error('No comment field found');

  // --- Step 2: Scroll and Fill ---
  try {
    const el = await page.$(commentSelector);
    if (el) {
      await el.scrollIntoView();
      await delay(1000);
    }
  } catch (e) {}

  // Pick a random natural comment
  const comment = pickRandom(COMMENT_TEMPLATES);
  console.log(`    📝 Filling comment: ${comment.substring(0, 30)}...`);
  await humanType(page, commentSelector, comment);
  await delay(300);

  // Pick a persona
  const persona = pickRandom(PERSONAS);

  // Fill name field
  const nameSelectors = [
    '#respond input[name="author"]', '#respond input#author',
    '.comment-respond input[name="author"]', '.comment-respond input#author',
    'input[name="author"]', 'input#author',
    'input[name*="name" i]', 'input[name*="author" i]',
    'input[placeholder*="name" i]',
    'input[id*="author" i]', 'input[id*="name" i]'
  ];
  for (const sel of nameSelectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        console.log(`    👤 Filling name: ${persona.name}`);
        await humanType(page, sel, persona.name);
        break;
      }
    } catch (e) { continue; }
  }
  await delay(200);

  // Fill email field
  const emailSelectors = [
    '#respond input[name="email"]', '#respond input#email',
    '.comment-respond input[name="email"]', '.comment-respond input#email',
    'input[name="email"]', 'input#email',
    'input[type="email"]', 'input[name*="email" i]',
    'input[id*="email" i]', 'input[placeholder*="email" i]'
  ];
  for (const sel of emailSelectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        console.log(`    📧 Filling email: ${persona.email}`);
        await humanType(page, sel, persona.email);
        break;
      }
    } catch (e) { continue; }
  }
  await delay(200);

  // Fill URL/website field with our site URL (this is the backlink!)
  if (norm.has_url_field) {
    const urlSelectors = [
      '#respond input[name="url"]', '#respond input#url',
      '.comment-respond input[name="url"]', '.comment-respond input#url',
      'input[name="url"]', 'input#url',
      'input[name*="website" i]', 'input[name*="url" i]',
      'input[type="url"]', 'input[placeholder*="website" i]',
      'input[placeholder*="url" i]',
      'input[id*="url" i]', 'input[id*="website" i]'
    ];
    for (const sel of urlSelectors) {
      try {
        const el = await page.$(sel);
        if (el && await el.isVisible()) {
          console.log(`    🔗 Filling website: ${site.url}`);
          await humanType(page, sel, site.url);
          break;
        }
      } catch (e) { continue; }
    }
  }
  await delay(500);

  // Submit the comment
  const submitSelectors = [
    'input#submit', 'input[name="submit"]',
    'button[type="submit"]', 'input[type="submit"]',
    'button:has-text("Post Comment")',
    'button:has-text("Submit")',
    'button:has-text("Post")',
    'button:has-text("Send")',
  ];
  let submitted = false;
  for (const sel of submitSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn && await btn.isVisible()) {
        await btn.click();
        submitted = true;
        await delay(3000);
        break;
      }
    } catch (e) { continue; }
  }
  if (!submitted) throw new Error('No submit button found');
}

// --- Blocker detection ---
async function checkBlockers(page) {
  const html = await page.content().catch(() => '');

  if (html.includes('recaptcha') || html.includes('hcaptcha') ||
      html.includes('g-recaptcha') || html.includes('cf-turnstile')) {
    return 'captcha';
  }

  // Check for closed comments (WordPress)
  const bodyText = await page.textContent('body').catch(() => '');
  if (bodyText.match(/comments.*closed/i) || bodyText.match(/comments.*disabled/i)) {
    return 'comments_closed';
  }

  return null;
}

// --- Process a single resource ---
async function processResource(resource, site, page, log) {
  const norm = normalizeResource(resource);
  const result = {
    url: norm.url,
    type: norm.type,
    site: site.name,
    site_url: site.url,
    timestamp: new Date().toISOString(),
    status: 'unknown',
  };

  try {
    console.log(`  🔄 ${norm.url.substring(0, 80)}`);

    // Skip profiles without URL fields (useless)
    if (norm.type === 'profile' && !norm.has_url_field) {
      result.status = 'skipped';
      result.reason = 'no_url_field';
      console.log(`    ⏭️  Skipped (profile, no URL field)`);
      return result;
    }

    // Skip captcha sites
    if (norm.has_captcha) {
      result.status = 'skipped';
      result.reason = 'captcha';
      console.log(`    ⏭️  Skipped (has captcha)`);
      return result;
    }

    // Pre-flight blocker check
    const blocker = await checkBlockers(page);
    if (blocker) {
      result.status = 'skipped';
      result.reason = blocker;
      console.log(`    ⏭️  Skipped (${blocker})`);
      return result;
    }

    // Navigate and check blockers
    if (norm.type === 'blog_comment') {
      await submitBlogComment(page, resource, site);
    } else {
      result.status = 'skipped';
      result.reason = 'unsupported_type';
      console.log(`    ⏭️  Skipped (type: ${norm.type})`);
      return result;
    }

    result.status = 'submitted';
    console.log(`    ✅ Submitted`);

  } catch (error) {
    const msg = error.message || '';
    if (msg.includes('Timeout') || msg.includes('timeout') || msg.includes('ETIMEDOUT')) {
      result.status = 'skipped';
      result.reason = 'timeout';
      console.log(`    ⏭️  Skipped (timeout/network)`);
    } else if (msg.includes('No comment field') || msg.includes('No submit button')) {
      result.status = 'skipped';
      result.reason = msg;
      console.log(`    ⏭️  Skipped (${msg})`);
    } else if (msg.includes('closed') || msg.includes('context or browser has been closed')) {
      // Critical browser error - stop the batch to prevent cascaded failures
      console.error(`\n🛑 CRITICAL BROWSER ERROR: ${msg}`);
      process.exit(1);
    } else {
      result.status = 'failed';
      result.error = msg;
      console.log(`    ❌ Failed: ${msg}`);
    }
  }

  return result;
}

// --- Main ---
async function batchSubmit(opts = {}) {
  const limit = opts.limit || 10;
  const siteIndex = opts.siteIndex ?? Math.floor(Math.random() * 3); // random site if not specified
  const dryRun = opts.dryRun || false;

  console.log('🚀 Batch Backlink Submission v2\n');

  const { resources, sites } = loadResources();
  const log = loadLog();
  const globalHistory = loadGlobalHistory();

  // Rotate through sites
  const site = sites[siteIndex % sites.length];
  console.log(`📍 Target: ${site.name} (${site.url})`);

  // Prioritize and filter
  const prioritized = prioritizeResources(resources);
  const pending = prioritized.filter(r => {
    const url = r.url || r.URL;
    return !isSubmitted(log, globalHistory, url, site.url);
  });

  // Only blog_comments with URL field and no captcha
  const actionable = pending.filter(r => {
    const norm = normalizeResource(r);
    return norm.type === 'blog_comment' && norm.has_url_field && !norm.has_captcha;
  });

  if (actionable.length === 0) {
    console.log('✨ No actionable resources remaining!');
    return;
  }

  console.log(`📊 Actionable: ${actionable.length} | Processing: ${Math.min(limit, actionable.length)}\n`);

  if (dryRun) {
    console.log('[DRY RUN] Would process:');
    actionable.slice(0, limit).forEach((r, i) =>
      console.log(`  ${i + 1}. ${(r.url || r.URL).substring(0, 80)}`)
    );
    return;
  }

  const toProcess = actionable.slice(0, limit);

  // Resolve engine from CLI args
  const sessionConfig = { browser: { headless: opts.visible ? false : true } };
  if (opts.engine) sessionConfig._engine = opts.engine;
  const { page, close } = await createSession(sessionConfig);

  try {
    for (let i = 0; i < toProcess.length; i++) {
      const resource = toProcess[i];
      console.log(`[${i + 1}/${toProcess.length}]`);

      const result = await processResource(resource, site, page, log);
      log.submissions.push(result);
      saveLog(log);

      if (opts.visible) {
        console.log('    👀 Pausing 5s for visibility...');
        await delay(5000);
      }

      // Track in global history using composite key
      const url = resource.url || resource.URL;
      const key = `${site.url}|${url}`;
      globalHistory.add(key);
      saveGlobalHistory(globalHistory);

      // Close tab after each site to keep browser clean
      await page.close();

      // Random delay
      if (i < toProcess.length - 1) {
        const delayMs = MIN_DELAY + Math.random() * (MAX_DELAY - MIN_DELAY);
        console.log(`    ⏳ ${Math.round(delayMs / 1000)}s...\n`);
        await delay(delayMs);
      }
    }
  } finally {
    await close();
  }

  // Summary
  const submitted = log.submissions.filter(s => s.status === 'submitted').length;
  const skipped = log.submissions.filter(s => s.status === 'skipped').length;
  const failed = log.submissions.filter(s => s.status === 'failed').length;

  console.log('\n📈 Summary:');
  console.log(`  ✅ Submitted: ${submitted}`);
  console.log(`  ⏭️  Skipped: ${skipped}`);
  console.log(`  ❌ Failed: ${failed}`);
  console.log(`  📁 Log: ${getLogPath()}\n`);
}

// CLI
import { fileURLToPath } from 'url';
import path from 'path';

if (import.meta.url === `file://${process.argv[1]}` || 
    fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const args = process.argv.slice(2);
  const opts = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--limit' || args[i] === '-l') { opts.limit = parseInt(args[++i], 10); }
    else if (args[i] === '--site' || args[i] === '-s') { opts.siteIndex = parseInt(args[++i], 10); }
    else if (args[i] === '--engine') { opts.engine = args[++i]; }
    else if (args[i] === '--dry-run') { opts.dryRun = true; }
    else if (args[i] === '--visible') { opts.visible = true; }
  }

  batchSubmit(opts).catch(err => {
    console.error('❌ Error:', err.message);
    process.exit(1);
  });
}

export { batchSubmit };
