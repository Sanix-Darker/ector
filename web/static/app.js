// ECTOR showcase front-end. Vanilla JS, no build step.
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const input = $("input");
  const output = $("output");
  const langSel = $("lang");
  const latency = $("latency");
  const counter = $("counter");

  let EXAMPLES = [];
  let lastPickIndex = -1;
  let lastResult = null; // last parsed object, for Copy JSON

  // ---------------------------------------------------------------- helpers
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[c]));
  }

  const CARET_SVG =
    '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>';

  // ---------------------------------------------------------------- theme
  const ICON_MOON =
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  const ICON_SUN =
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    $("theme-toggle").innerHTML = theme === "dark" ? ICON_SUN : ICON_MOON;
  }
  function initTheme() {
    const stored = localStorage.getItem("ector-theme");
    applyTheme(stored === "dark" ? "dark" : "light");
  }
  function toggleTheme() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("ector-theme", next);
    applyTheme(next);
  }

  // ---------------------------------------------------------------- JSON tree
  // Renders an object/array into collapsible rows with line numbers.
  function valueHtml(v) {
    if (v === null) return '<span class="tok-bool">null</span>';
    const t = typeof v;
    if (t === "number") return '<span class="tok-num">' + v + "</span>";
    if (t === "boolean") return '<span class="tok-bool">' + v + "</span>";
    return '<span class="tok-str">"' + escapeHtml(v) + '"</span>';
  }

  function isContainer(v) {
    return v !== null && typeof v === "object";
  }

  function summaryFor(v) {
    if (Array.isArray(v)) return v.length + (v.length === 1 ? " item" : " items");
    return Object.keys(v).length + (Object.keys(v).length === 1 ? " key" : " keys");
  }

  // Build rows recursively. Each row is {depth, html, group, opener}.
  function buildRows(value) {
    const rows = [];
    let gid = 0;

    function indent(depth) {
      return '<span class="jindent">' + "  ".repeat(depth) + "</span>";
    }

    function pushLeaf(depth, prefixHtml, valHtml, trailing) {
      rows.push({
        depth,
        toggleable: false,
        group: null,
        parents: [],
        html: indent(depth) +
          '<span class="jcaret empty">' + CARET_SVG + "</span>" +
          prefixHtml + valHtml + (trailing || ""),
      });
    }

    function walk(value, depth, keyPrefixHtml, parents, trailing) {
      const open = Array.isArray(value) ? "[" : "{";
      const close = Array.isArray(value) ? "]" : "}";
      if (!isContainer(value)) {
        pushLeaf(depth, keyPrefixHtml, valueHtml(value), trailing);
        return;
      }
      const myId = ++gid;
      const entries = Array.isArray(value)
        ? value.map((v, i) => [null, v])
        : Object.keys(value).map((k) => [k, value[k]]);

      // opening line (toggleable)
      rows.push({
        depth,
        toggleable: entries.length > 0,
        group: myId,
        parents: parents.slice(),
        openLine: true,
        html: indent(depth) +
          '<span class="jcaret">' + CARET_SVG + "</span>" +
          keyPrefixHtml +
          '<span class="jbracket">' + open + "</span>" +
          '<span class="jsummary"> ' + (entries.length ? "" : "") + "</span>",
        summaryText: " " + summaryFor(value) + " ",
        open: open,
        close: close,
      });

      const childParents = parents.concat(myId);
      entries.forEach(([k, v], idx) => {
        const isLast = idx === entries.length - 1;
        const tail = isLast ? "" : '<span class="jpunc">,</span>';
        const kp = k === null
          ? ""
          : '<span class="tok-key">"' + escapeHtml(k) + '"</span><span class="jpunc">: </span>';
        walk(v, depth + 1, kp, childParents, tail);
      });

      // closing line
      rows.push({
        depth,
        toggleable: false,
        group: null,
        parents: childParents.slice(),
        closeFor: myId,
        html: indent(depth) +
          '<span class="jcaret empty">' + CARET_SVG + "</span>" +
          '<span class="jbracket">' + close + "</span>" + (trailing || ""),
      });
    }

    walk(value, 0, "", [], "");
    return rows;
  }

  const collapsed = new Set(); // group ids currently collapsed

  function renderTree() {
    if (!lastResult) return;
    const rows = buildRows(lastResult);
    const frag = document.createDocumentFragment();
    let lineNo = 0;

    rows.forEach((row) => {
      // hidden if any ancestor group is collapsed
      const hiddenByParent = row.parents.some((p) => collapsed.has(p));
      // a collapsed group's own children/closing are hidden; opening stays
      if (hiddenByParent) return;

      lineNo += 1;
      const el = document.createElement("div");
      el.className = "jrow";
      if (row.toggleable) {
        el.classList.add("toggleable");
        el.tabIndex = 0;
        el.setAttribute("role", "treeitem");
        el.setAttribute("aria-expanded", collapsed.has(row.group) ? "false" : "true");
      }
      let contentHtml = row.html;
      if (row.openLine && collapsed.has(row.group)) {
        el.classList.add("collapsed");
        contentHtml = contentHtml.replace(
          '<span class="jsummary"> </span>',
          '<span class="jsummary">' + row.summaryText + "</span>" +
            '<span class="jbracket">' + row.close + "</span>"
        );
      }
      el.innerHTML =
        '<span class="jln">' + lineNo + "</span>" +
        '<span class="jcontent">' + contentHtml + "</span>";

      if (row.toggleable) {
        const gid = row.group;
        const toggle = () => {
          if (collapsed.has(gid)) collapsed.delete(gid);
          else collapsed.add(gid);
          renderTree();
        };
        el.addEventListener("click", toggle);
        el.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggle();
          }
        });
      }
      frag.appendChild(el);
    });

    output.innerHTML = "";
    output.appendChild(frag);
  }

  function allGroupIds() {
    const ids = new Set();
    let gid = 0;
    (function walk(v) {
      if (!isContainer(v)) return;
      gid += 1;
      const myId = gid;
      ids.add(myId);
      const vals = Array.isArray(v) ? v : Object.values(v);
      vals.forEach(walk);
    })(lastResult);
    return ids;
  }

  function expandAll() {
    collapsed.clear();
    renderTree();
  }
  function collapseAll() {
    // collapse everything except the root (group id 1) so the structure is visible
    const ids = allGroupIds();
    collapsed.clear();
    ids.forEach((id) => {
      if (id !== 1) collapsed.add(id);
    });
    renderTree();
  }

  // ---------------------------------------------------------------- counter
  function localWordCount(text) {
    const t = text.trim();
    return t ? t.split(/\s+/).length : 0;
  }
  function setCounter(words, tokens, chars) {
    const tok = tokens === null ? "…" : tokens;
    counter.innerHTML =
      '<span class="num">' + words + "</span> words · " +
      '<span class="num">' + tok + "</span> tokens · " +
      '<span class="num">' + chars + "</span> chars";
  }

  let tokenReq = 0;
  let tokenTimer = null;
  function updateCounts() {
    const text = input.value;
    const words = localWordCount(text);
    const chars = text.length;
    if (!text.trim()) {
      setCounter(0, 0, 0);
      return;
    }
    setCounter(words, null, chars);
    clearTimeout(tokenTimer);
    const reqId = ++tokenReq;
    tokenTimer = setTimeout(async () => {
      try {
        const res = await fetch("/api/tokenize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, lang: langSel.value }),
        });
        if (!res.ok) throw new Error("tokenize failed (" + res.status + ")");
        const data = await res.json();
        if (reqId !== tokenReq) return;
        setCounter(data.words, data.tokens, data.chars);
      } catch (e) {
        if (reqId === tokenReq) setCounter(words, words, chars);
      }
    }, 250);
  }

  // ---------------------------------------------------------------- compute
  async function compute() {
    const text = input.value.trim();
    if (!text) {
      lastResult = null;
      output.innerHTML = '<span class="muted">// Enter a request first</span>';
      return;
    }
    output.innerHTML = '<span class="muted">// parsing…</span>';
    const t0 = performance.now();
    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, lang: langSel.value }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        const message = payload && payload.detail ? payload.detail : "extract failed (" + res.status + ")";
        throw new Error(message);
      }
      const data = await res.json();
      const dt = (performance.now() - t0).toFixed(1);
      lastResult = data;
      collapsed.clear();
      renderTree();
      latency.textContent = "Parsed in " + dt + " ms (round-trip)";
    } catch (e) {
      lastResult = null;
      output.innerHTML = '<span class="muted">// error: ' + escapeHtml(String(e)) + "</span>";
    }
  }

  function fillAndRun(text, lang) {
    input.value = text;
    if (lang) langSel.value = lang;
    input.classList.add("flash");
    setTimeout(() => input.classList.remove("flash"), 600);
    updateCounts();
    compute();
  }

  // ---------------------------------------------------------------- copy
  function copyText(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      const old = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = old), 1200);
    });
  }

  function initCodeCopyButtons() {
    document.querySelectorAll("[data-copy-code]").forEach((btn) => {
      const code = btn.closest(".code-block")?.querySelector("code");
      if (!code) return;
      btn.addEventListener("click", (e) => copyText(code.innerText.trim(), e.target));
    });
  }

  // ---------------------------------------------------------------- examples
  function byLang() {
    const groups = {};
    EXAMPLES.forEach((ex) => (groups[ex.lang] || (groups[ex.lang] = [])).push(ex));
    return groups;
  }

  function renderExamples() {
    const wrap = $("examples");
    wrap.innerHTML = "";
    const groups = byLang();
    const tags = { en: "EN", fr: "FR" };
    Object.keys(groups).forEach((lang) => {
      if (!groups[lang].length) return;
      const row = document.createElement("div");
      row.className = "example-group";
      const tag = document.createElement("span");
      tag.className = "example-group-tag";
      tag.textContent = tags[lang] || lang.toUpperCase();
      row.appendChild(tag);
      const chips = document.createElement("div");
      chips.className = "example-chips";
      groups[lang].forEach((ex) => {
        const chip = document.createElement("button");
        chip.className = "chip";
        chip.textContent = ex.label.replace(/\s*\((EN|FR)\)\s*$/, "");
        chip.title = ex.text;
        chip.addEventListener("click", () => fillAndRun(ex.text, ex.lang));
        chips.appendChild(chip);
      });
      row.appendChild(chips);
      wrap.appendChild(row);
    });
  }

  function randomPick() {
    if (!EXAMPLES.length) return;
    let i = Math.floor(Math.random() * EXAMPLES.length);
    if (EXAMPLES.length > 1 && i === lastPickIndex) i = (i + 1) % EXAMPLES.length;
    lastPickIndex = i;
    const ex = EXAMPLES[i];
    fillAndRun(ex.text, ex.lang);
  }

  function combineSamples() {
    if (!EXAMPLES.length) return;
    const groups = byLang();
    const eligible = Object.keys(groups).filter((l) => groups[l].length >= 2);
    if (!eligible.length) {
      randomPick();
      return;
    }
    const lang = eligible[Math.floor(Math.random() * eligible.length)];
    const pool = groups[lang].slice();
    const a = pool.splice(Math.floor(Math.random() * pool.length), 1)[0];
    const b = pool.splice(Math.floor(Math.random() * pool.length), 1)[0];
    const join = (s) => s.trim().replace(/[.\s]+$/, "");
    fillAndRun(join(a.text) + ". " + join(b.text), lang);
  }

  async function loadExamples() {
    try {
      const res = await fetch("/api/examples");
      const data = await res.json();
      EXAMPLES = data.examples || [];
      renderExamples();
    } catch (e) {
      /* ignore */
    }
  }

  async function loadHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      $("version").textContent = "v" + data.version;
      if (data.repo) $("repo-link").href = data.repo;
    } catch (e) {
      /* ignore */
    }
  }

  // ---------------------------------------------------------------- wire-up
  $("compute").addEventListener("click", compute);
  $("theme-toggle").addEventListener("click", toggleTheme);
  $("combine").addEventListener("click", combineSamples);
  $("random").addEventListener("click", randomPick);
  $("expand-all").addEventListener("click", expandAll);
  $("collapse-all").addEventListener("click", collapseAll);
  input.addEventListener("input", updateCounts);
  langSel.addEventListener("change", updateCounts);
  input.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") compute();
  });
  $("copy-install").addEventListener("click", (e) =>
    copyText($("install-cmd").textContent, e.target)
  );
  $("copy-json").addEventListener("click", (e) =>
    copyText(lastResult ? JSON.stringify(lastResult, null, 2) : "", e.target)
  );

  initTheme();
  updateCounts();
  initCodeCopyButtons();
  loadExamples();
  loadHealth();
})();
