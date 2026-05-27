#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { createSession, delay } from './browser.js';

const TIMEOUT_MS = 30000;

function loadResources() {
  if (!existsSync('resources/backlink-resources.json')) {
    console.error('❌ resources/backlink-resources.json not found.');
    process.exit(1);
  }
  const raw = JSON.parse(readFileSync('resources/backlink-resources.json', 'utf-8'));
  return Array.isArray(raw) ? raw : [...(raw.profiles || []), ...(raw.blog_comments || [])];
}

async function checkCommentArea(page, url) {
  console.log(`\n🔍 Checking: ${url}`);
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: TIMEOUT_MS });
    await delay(3000); // Wait for lazy load

    // If URL has a comment hash, try to scroll to it
    if (url.includes('#comment-')) {
      const hash = url.split('#')[1];
      await page.evaluate((id) => {
        const el = document.getElementById(id) || document.querySelector(`[name="${id}"]`);
        if (el) el.scrollIntoView({ behavior: 'auto', block: 'center' });
      }, hash);
      await delay(1000);
    }

    const strategies = [
      { name: 'Standard Textarea', selector: 'textarea[name="comment"], textarea#comment' },
      { name: 'Fuzzy Comment', selector: 'textarea[name*="comment" i], textarea[id*="comment" i]' },
      { name: 'Message Field', selector: 'textarea[name*="message" i]' },
      { name: 'Placeholder Match', selector: 'textarea[placeholder*="comment" i]' },
      { name: 'WordPress Respond', selector: '#respond textarea, .comment-respond textarea' },
      { name: 'Generic Textarea', selector: 'textarea' },
      { name: 'Iframe Comment', selector: 'iframe[title*="comment" i], iframe[id*="comment" i]' }
    ];

    let found = false;
    for (const strat of strategies) {
      try {
        const isVisible = await page.evaluate((sel) => {
          const el = document.querySelector(sel);
          return el && el.offsetWidth > 0 && el.offsetHeight > 0;
        }, strat.selector);

        if (isVisible === 'true') {
          console.log(`  ✅ Found: ${strat.name} (${strat.selector})`);
          // Highlight it in the browser
          await page.evaluate((sel) => {
            const el = document.querySelector(sel);
            if (el) {
              el.style.border = '5px solid red';
              el.scrollIntoView({ behavior: 'auto', block: 'center' });
            }
          }, strat.selector);
          found = true;
          break;
        }
      } catch (e) {}
    }

    if (!found) {
      console.log('  ❌ NO comment area found with standard strategies.');
      
      // Deep scout: check for any button/link that might open comments
      const potentialButtonsJson = await page.evaluate(() => {
        const keywords = ['comment', 'reply', 'respond', 'leave', 'feedback'];
        const elements = Array.from(document.querySelectorAll('button, a, span'))
          .filter(el => {
            const text = (el.innerText || '').toLowerCase();
            return keywords.some(k => text.includes(k)) && el.offsetWidth > 0;
          })
          .map(el => ({
            tag: el.tagName,
            text: el.innerText.substring(0, 30),
            id: el.id,
            class: el.className
          }));
        return JSON.stringify(elements.slice(0, 5));
      });
      const potentialButtons = JSON.parse(potentialButtonsJson);
      if (potentialButtons.length > 0) {
        console.log(`  🔘 Potential interaction elements: ${JSON.stringify(potentialButtons, null, 2)}`);
      }

      // Check for any textarea even if hidden
      const anyTextareaJson = await page.evaluate(() => {
        const t = document.querySelector('textarea');
        if (!t) return 'null';
        return JSON.stringify({ 
          outer: (t.outerHTML || '').substring(0, 100), 
          visible: (t.offsetWidth > 0 && t.offsetHeight > 0) 
        });
      });
      if (anyTextareaJson !== 'null') {
        const anyTextarea = JSON.parse(anyTextareaJson);
        console.log(`  💡 Found a textarea: ${anyTextarea.outer}... (Visible: ${anyTextarea.visible})`);
      }
    }

    return found;

  } catch (error) {
    console.log(`  ⚠️ Error visiting page: ${error.message}`);
    return false;
  }
}

async function main() {
  const args = process.argv.slice(2);
  let limit = 10;
  let testUrl = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url') {
      testUrl = args[++i];
    } else if (!isNaN(parseInt(args[i]))) {
      limit = parseInt(args[i]);
    }
  }

  const resources = loadResources();
  let actionable;
  
  if (testUrl) {
    actionable = [{ url: testUrl, type: 'blog_comment' }];
    limit = 1;
  } else {
    actionable = resources.filter(r => (r.type === 'blog_comment' || r.Type === 'blog_comment') && !r.submitted);
  }

  console.log(`🚀 Starting Reconnaissance on ${Math.min(limit, actionable.length)} sites...\n`);

  const { page, close } = await createSession({ _engine: 'bb' });

  try {
    let successCount = 0;
    const results = [];
    for (let i = 0; i < Math.min(limit, actionable.length); i++) {
      console.log(`[${i + 1}/${limit}]`);
      const url = actionable[i].url || actionable[i].URL;
      const ok = await checkCommentArea(page, url);
      if (ok) successCount++;
      results.push({ url, status: ok ? 'SUCCESS' : 'FAILED' });
      
      // Close tab after each site to keep browser clean
      await page.close();
      await delay(1000);
    }
    
    const summary = `\n📊 Recon Summary: Found comment area on ${successCount}/${Math.min(limit, actionable.length)} sites.`;
    console.log(summary);
    
    writeFileSync('recon-results.log', results.map(r => `${r.status}: ${r.url}`).join('\n') + summary);
    console.log('📝 Results saved to recon-results.log');
  } finally {
    await close();
  }
}

main().catch(err => console.error(err));
