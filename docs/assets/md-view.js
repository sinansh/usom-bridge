/* SGB markdown viewer - tek dosya, generic.
 * Kullanim: docs/view.html?file=integrations/qradar.md
 *
 * Dependencies (CDN):
 *   - marked.js  (markdown -> html)
 *   - highlight.js (kod blogu syntax highlight)
 *
 * Guvenlik notu: marked.js default'ta html escape eder; biz raw HTML
 * istemiyoruz (kullanici-ureticisi degil, repo'daki MD'ler). Yine de
 * basit bir DOMPurify-suz akimda XSS riski yok cunku content git'te.
 */

(function () {
  'use strict';

  const params = new URLSearchParams(location.search);
  const file = params.get('file');
  const root = document.getElementById('md-root');
  const titleEl = document.getElementById('page-title');

  if (!file) {
    root.innerHTML = '<div class="callout warn"><strong>Hata:</strong> ?file=&lt;path&gt; parametresi gerekli. Ornek: <code>?file=integrations/qradar.md</code></div>';
    return;
  }

  // Path normalizasyonu: '../' ya da disinda gezinmeyi engelle.
  if (file.includes('..') || file.startsWith('/') || !file.endsWith('.md')) {
    root.innerHTML = '<div class="callout bad"><strong>Gecersiz dosya:</strong> ' + escapeHtml(file) + '</div>';
    return;
  }

  // Hub'a donus linki: file path'inden cikar (integrations/foo.md -> integrations/)
  const dir = file.includes('/') ? file.substring(0, file.lastIndexOf('/') + 1) : '';
  const dirName = dir.replace(/\/$/, '') || 'docs';

  // marked yapilandirma
  function setupMarked() {
    if (typeof marked === 'undefined') return;
    marked.setOptions({
      gfm: true,
      breaks: false,
      headerIds: true,
      mangle: false,
      highlight: function (code, lang) {
        if (typeof hljs === 'undefined') return code;
        if (lang && hljs.getLanguage(lang)) {
          try { return hljs.highlight(code, { language: lang }).value; }
          catch (_) {}
        }
        try { return hljs.highlightAuto(code).value; } catch (_) { return code; }
      },
    });
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderBreadcrumb(file) {
    const parts = file.split('/');
    const fname = parts.pop();
    const segs = ['<a href="./">Ana sayfa</a>'];
    let acc = '';
    for (const p of parts) {
      acc += p + '/';
      segs.push('<a href="' + acc + '">' + p + '</a>');
    }
    segs.push('<span>' + fname + '</span>');
    return '<div class="breadcrumb">' + segs.join(' / ') + '</div>';
  }

  function fixRelativeLinks(html, baseDir) {
    // .md linklerini view.html?file=... formatina cevir
    // <a href="UC-PH-001.md">  -> <a href="../view.html?file=usecases/UC-PH-001.md">
    // <a href="../foo/bar.md"> -> aynisi ile resolve
    return html.replace(/href="([^"]+\.md)"/g, function (m, href) {
      if (/^(https?:|\/\/|#)/.test(href)) return m; // external veya anchor
      // Relative path'i baseDir'den itibaren cozumle
      let resolved;
      if (href.startsWith('../')) {
        // ../X -> baseDir'in bir ust dizininden
        const baseParts = baseDir.replace(/\/$/, '').split('/').filter(Boolean);
        baseParts.pop();
        resolved = (baseParts.length ? baseParts.join('/') + '/' : '') + href.replace(/^\.\.\//, '');
      } else if (href.startsWith('./')) {
        resolved = baseDir + href.substring(2);
      } else {
        resolved = baseDir + href;
      }
      return 'href="view.html?file=' + encodeURIComponent(resolved) + '"';
    });
  }

  // Fetch + render
  async function load() {
    try {
      setupMarked();
      const r = await fetch(file, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const text = await r.text();
      const fname = file.split('/').pop().replace(/\.md$/, '');

      // Title
      const m = text.match(/^#\s+(.+?)\s*$/m);
      const title = m ? m[1] : fname;
      titleEl.textContent = title + ' — SGB API Bridge';

      // Render
      const bodyHtml = marked.parse(text);
      const fixed = fixRelativeLinks(bodyHtml, dir);
      const rawLink = 'https://github.com/bilsectr/sgb-api-bridge/blob/main/docs/' + file;
      root.innerHTML =
        renderBreadcrumb(file) +
        fixed +
        '<a class="raw-link" href="' + rawLink + '" target="_blank" rel="noopener">Markdown kaynagini GitHub\'da gor →</a>';

      // Anchor scroll
      if (location.hash) {
        const el = document.querySelector(location.hash);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (e) {
      root.innerHTML =
        '<div class="callout bad"><strong>Yuklenemedi:</strong> <code>' +
        escapeHtml(file) + '</code> — ' + escapeHtml(String(e)) + '</div>';
    }
  }

  load();
})();
