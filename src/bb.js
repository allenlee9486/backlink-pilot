// bb.js — bb-browser execution layer
// Wraps bb-browser CLI as subprocess calls, exposes Playwright-like page API

import { spawnSync } from 'child_process';

let _bbTimeout = 30000;

function setBbTimeout(ms) {
  if (ms && ms > 0) _bbTimeout = ms;
}

function bb(...args) {
  try {
    const isWin = process.platform === 'win32';
    const cmd = isWin ? 'bb-browser.cmd' : 'bb-browser';
    
    // On Windows, we need to be very careful with arguments.
    // spawnSync with shell: true handles .cmd files, but argument quoting is tricky.
    const result = spawnSync(cmd, args, {
      encoding: 'utf-8',
      timeout: _bbTimeout,
      shell: isWin,
      // On Windows, use windowsVerbatimArguments to prevent double-quoting issues
      // when passing complex JS strings to bb-browser
      ...(isWin ? { windowsVerbatimArguments: false } : {})
    });

    if (result.error) throw result.error;

    if (result.status !== 0) {
      const msg = result.stderr?.trim() || result.stdout?.trim() || 'Unknown error';
      throw new Error(msg);
    }

    return result.stdout.trim();
  } catch (e) {
    const msg = e.stderr?.trim() || e.message;
    if (msg.includes('ECONNREFUSED') || msg.includes('No page target') || msg.includes('connect')) {
      throw new Error(
        `bb-browser cannot connect to Chrome. Make sure it is running:\n` +
        `  1. Run: bb-browser status\n` +
        `  2. If no Chrome is running: bb-browser open about:blank\n` +
        `  3. Try again`
      );
    }
    if (msg.includes('超时') || msg.includes('timeout') || msg.includes('ETIMEDOUT') || e.killed) {
      throw new Error(
        `bb-browser command timed out (${args.join(' ')}). Chrome may be unresponsive.\n` +
        `  Try: kill the Chrome process and restart with bb-browser open about:blank`
      );
    }
    throw new Error(`bb-browser ${args[0]}: ${msg}`);
  }
}

function escapeJs(str) {
  return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

/**
 * Check if bb-browser is available on the system
 */
export function isBbAvailable() {
  try {
    const isWin = process.platform === 'win32';
    const cmd = isWin ? 'bb-browser.cmd' : 'bb-browser';
    const result = spawnSync(cmd, ['--version'], { 
      encoding: 'utf-8',
      shell: isWin 
    });
    return result.status === 0;
  } catch { return false; }
}

/**
 * Playwright-like page wrapper around bb-browser CLI
 */
export class BbPage {
  constructor(config = {}) {
    this._config = config;
    this._tabId = null;
    this._openedTabs = []; // track tabs for cleanup

    // Apply timeout from config
    if (config.browser?.timeout) setBbTimeout(config.browser.timeout);

    // Verify Chrome is reachable — use 'tab list' instead of 'status'
    // because 'status' can return "running" even when commands timeout
    try {
      bb('tab', 'list');
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('超时') || msg.includes('timeout') || msg.includes('Timeout')) {
        throw new Error(
          `bb-browser Chrome is not responding (commands timeout).\n` +
          `  Try restarting Chrome:\n` +
          `    1. Kill the managed Chrome: kill $(cat ~/.bb-browser/browser/cdp-port 2>/dev/null && lsof -ti :19825)\n` +
          `    2. Relaunch: bb-browser open about:blank\n` +
          `    3. Retry your command.`
        );
      }
      throw new Error(
        `bb-browser Chrome is not running.\n` +
        `  Start it with: bb-browser open about:blank\n` +
        `  Then retry your command.`
      );
    }
  }

  async goto(url, _opts = {}) {
    const result = bb('open', url, '--tab');
    // Extract tabId from output like "Tab ID: XXXX"
    const tabMatch = result.match(/Tab ID:\s*(\S+)/);
    if (tabMatch) {
      this._tabId = tabMatch[1];
      this._openedTabs.push(this._tabId);
    }
    // Wait for page to settle (no networkidle equivalent)
    await new Promise(r => setTimeout(r, 2000));
  }

  /**
   * Close all tabs opened during this session
   */
  async cleanup() {
    for (const tabId of this._openedTabs) {
      try { bb('close', '--tab', tabId); } catch {}
    }
    this._openedTabs = [];
  }

  async fill(selectorOrRef, value) {
    const args = ['fill', selectorOrRef, value];
    if (this._tabId) args.unshift('--tab', this._tabId);

    if (selectorOrRef.startsWith('@')) {
      bb(...args);
    } else {
      // CSS selector — find element via eval, then use ref from snapshot
      const ref = await this._resolveRef(selectorOrRef);
      if (ref) {
        // Find 'fill' in args and replace the selectorOrRef part
        const fillIdx = args.indexOf('fill');
        args[fillIdx + 1] = ref;
        bb(...args);
      }
      else throw new Error(`Element not found: ${selectorOrRef}`);
    }
  }

  async click(selectorOrRef) {
    if (selectorOrRef.startsWith('@')) {
      const args = ['click', selectorOrRef];
      if (this._tabId) args.unshift('--tab', this._tabId);
      bb(...args);
    } else {
      // CSS selector — use evalClick with full user-event simulation
      // This dispatches mousedown/mouseup/click to work with React/Vue components
      await this.evalClickReal(selectorOrRef);
    }
  }

  async type(selectorOrRef, text, _opts = {}) {
    // bb-browser fill handles typing in real browser
    await this.fill(selectorOrRef, text);
  }

  async textContent(selector) {
    return this._eval(`document.querySelector('${escapeJs(selector)}')?.textContent || ''`);
  }

  async content() {
    return this._eval('document.documentElement.outerHTML');
  }

  url() {
    return this._eval('window.location.href');
  }

  async screenshot(path) {
    const args = ['screenshot'];
    if (path) args.push(path);
    if (this._tabId) args.unshift('--tab', this._tabId);
    bb(...args);
  }

  async evaluate(fn, ...args) {
    const code = `(${fn.toString()})(${args.map(a => JSON.stringify(a)).join(',')})`;
    return this._eval(code);
  }

  /**
   * Get interactive snapshot — returns parsed accessibility tree text
   */
  async snapshot() {
    const args = ['snapshot', '-i'];
    if (this._tabId) args.unshift('--tab', this._tabId);
    return bb(...args);
  }

  /**
   * Playwright-compatible $(selector) — returns BbElementHandle or null
   */
  async $(selector) {
    // Handle Playwright-specific :has-text() selector
    if (selector.includes(':has-text(')) {
      return this._queryHasText(selector);
    }
    const exists = this._eval(
      `!!document.querySelector('${escapeJs(selector)}')`);
    if (exists === 'true') return new BbElementHandle(this, selector);
    return null;
  }

  /**
   * Playwright-compatible locator(selector)
   */
  locator(selector) {
    return new BbLocator(this, selector);
  }

  // --- Internal helpers ---

  async _resolveRef(selector) {
    // Take snapshot and find matching element ref
    const snap = await this.snapshot();
    // Try direct eval to check existence first
    const exists = this._eval(`!!document.querySelector('${escapeJs(selector)}')`);
    if (exists !== 'true') return null;

    // Use eval to click/fill by selector directly
    // bb-browser supports CSS selectors via eval workaround
    return null; // fall through to eval-based approach
  }

  async _queryHasText(selector) {
    // Parse "button:has-text("Submit")" → tag=button, text=Submit
    const match = selector.match(/^(\w+):has-text\(["'](.+?)["']\)$/);
    if (!match) return null;
    const [, tag, text] = match;
    const exists = this._eval(
      `!!Array.from(document.querySelectorAll('${tag}')).find(el => el.textContent.includes('${escapeJs(text)}'))`);
    if (exists === 'true') return new BbElementHandle(this, selector, { tag, text });
    return null;
  }

  /**
   * Execute JS directly in page and fill/click by CSS selector
   */
  async evalFill(selector, value) {
    this._eval(`(() => {
      const el = document.querySelector('${escapeJs(selector)}');
      if (!el) return;
      el.focus();
      el.value = '${escapeJs(value)}';
      el.dispatchEvent(new Event('input', {bubbles: true}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
    })()`);
  }

  async evalClick(selector) {
    this._eval(`document.querySelector('${escapeJs(selector)}')?.click()`);
  }

  /**
   * Click with full user-event simulation (mousedown → mouseup → click)
   * Required for React/Vue components that don't respond to .click()
   */
  async evalClickReal(selector) {
    this._eval(`(() => {
      const el = document.querySelector('${escapeJs(selector)}');
      if (!el) return;
      el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true,cancelable:true}));
      el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true,cancelable:true}));
      el.dispatchEvent(new MouseEvent('click', {bubbles:true,cancelable:true}));
      if (el.type === 'radio' || el.type === 'checkbox') {
        el.checked = el.type === 'radio' ? true : !el.checked;
        el.dispatchEvent(new Event('change', {bubbles:true}));
        el.dispatchEvent(new Event('input', {bubbles:true}));
      }
    })()`);
  }

  async evalClickByText(tag, text) {
    this._eval(`Array.from(document.querySelectorAll('${tag}')).find(el => el.textContent.includes('${escapeJs(text)}'))?.click()`);
  }

  _eval(code) {
    // Base64 encode the code to avoid quoting issues on Windows CLI
    const b64 = Buffer.from(code).toString('base64');
    const wrapper = `eval(atob('${b64}'))`;
    const args = ['eval', wrapper];
    if (this._tabId) args.unshift('--tab', this._tabId);
    return bb(...args);
  }
}

/**
 * Element handle wrapping bb-browser eval calls
 */
export class BbElementHandle {
  constructor(page, selector, opts = {}) {
    this._page = page;
    this._selector = selector;
    this._tag = opts.tag;
    this._text = opts.text;
  }

  async isVisible() {
    if (this._tag && this._text) {
      return this._page._eval(
        `(() => {
          const el = Array.from(document.querySelectorAll('${this._tag}')).find(e => e.textContent.includes('${escapeJs(this._text)}'));
          if (!el) return false;
          const style = window.getComputedStyle(el);
          if (style.display === 'none' || style.visibility === 'hidden') return false;
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        })()`
      ) === 'true';
    }
    return this._page._eval(
      `(() => {
        const el = document.querySelector('${escapeJs(this._selector)}');
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      })()`
    ) === 'true';
  }

  async textContent() {
    if (this._tag && this._text) {
      return this._page._eval(
        `Array.from(document.querySelectorAll('${this._tag}')).find(e => e.textContent.includes('${escapeJs(this._text)}'))?.textContent || ''`);
    }
    return this._page._eval(
      `document.querySelector('${escapeJs(this._selector)}')?.textContent || ''`);
  }

  async getAttribute(attr) {
    return this._page._eval(
      `document.querySelector('${escapeJs(this._selector)}')?.getAttribute('${escapeJs(attr)}') || null`);
  }

  async click() {
    if (this._tag && this._text) {
      await this._page.evalClickByText(this._tag, this._text);
    } else {
      await this._page.evalClickReal(this._selector);
    }
  }

  async fill(value) {
    await this._page.evalFill(this._selector, value);
  }

  async scrollIntoView() {
    await this._page._eval(`(() => {
      const el = document.querySelector('${escapeJs(this._selector)}');
      if (!el) return;
      // Scroll to element and account for potential sticky headers
      el.scrollIntoView({ behavior: 'auto', block: 'center' });
      // If it's still covered or near top, nudge it down
      window.scrollBy(0, -100); 
    })()`);
    await new Promise(r => setTimeout(r, 1000));
  }

  async evaluate(fn) {
    // Simple evaluate — runs fn as string with el as argument
    return this._page._eval(
      `(${fn.toString()})(document.querySelector('${escapeJs(this._selector)}'))`);
  }
}

/**
 * Locator wrapping bb-browser eval calls
 */
export class BbLocator {
  constructor(page, selector) {
    this._page = page;
    this._selector = selector;
  }

  first() {
    return new BbElementHandle(this._page, this._selector);
  }

  async all() {
    const countStr = this._page._eval(
      `document.querySelectorAll('${escapeJs(this._selector)}').length`);
    const count = parseInt(countStr, 10) || 0;
    return Array.from({ length: count }, (_, i) =>
      new BbElementHandle(this._page,
        `document.querySelectorAll('${escapeJs(this._selector)}')[${i}]`)
    );
  }

  async isVisible() {
    return this._page._eval(
      `(() => {
        const el = document.querySelector('${escapeJs(this._selector)}');
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      })()`
    ) === 'true';
  }

  async fill(value) {
    await this._page.evalFill(this._selector, value);
  }

  async click() {
    await this._page.evalClickReal(this._selector);
  }
}
