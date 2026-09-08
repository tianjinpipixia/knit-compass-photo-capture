(function knitCompassYarnNameOnlyUiPatch() {
  "use strict";

  const BUILD = "2026-09-08-yarn-name-only-2";
  let queued = false;

  function clean(value) {
    return String(value == null ? "" : value).trim();
  }

  function replaceExactText(root, from, to) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const matches = [];
    let node;
    while ((node = walker.nextNode())) {
      if (clean(node.nodeValue) === from) matches.push(node);
    }
    matches.forEach(textNode => {
      const original = textNode.nodeValue || "";
      const leading = original.match(/^\s*/)?.[0] || "";
      const trailing = original.match(/\s*$/)?.[0] || "";
      textNode.nodeValue = `${leading}${to}${trailing}`;
    });
  }

  function patch() {
    const app = document.getElementById("app");
    if (!app) return;

    // Preserve the existing yarn_name data key and stored data; unify only the visible field wording.
    replaceExactText(app, "糸名・素材名", "糸名");

    const yarnInput = app.querySelector('input[name="yarn_name"]');
    if (yarnInput) {
      if (yarnInput.placeholder === "素材名または糸名を入力") yarnInput.placeholder = "糸名を入力";
      yarnInput.setAttribute("aria-label", "糸名");
      yarnInput.dataset.yarnNameUi = BUILD;
    }
  }

  function schedulePatch() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      patch();
    });
  }

  const app = document.getElementById("app");
  if (app) {
    new MutationObserver(schedulePatch).observe(app, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedulePatch, { once: true });
  } else {
    schedulePatch();
  }
})();
