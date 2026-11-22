// Sends the page's text to the local scoring server (127.0.0.1 only) and lists crash
// sentences with their labels and evidence. Suggestions are marked as suggestions.
const SERVER = "http://127.0.0.1:8765/score";
const out = document.getElementById("out");

function pageText() {
  const root = document.querySelector("article") || document.querySelector("main") || document.body;
  const h1 = document.querySelector("h1");
  return {
    title: (h1 && h1.innerText.trim()) || document.title,
    text: root.innerText,
    lang: (document.documentElement.lang || "en").slice(0, 2).toLowerCase(),
  };
}

function el(tag, attrs = {}, text = "") {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text) e.textContent = text;
  return e;
}

function render(sentences) {
  out.replaceChildren();
  if (!sentences.length) {
    out.append(el("p", { class: "muted" }, "No crash-describing sentences found."));
    return;
  }
  for (const s of sentences) {
    const box = el("div", { class: "sent" });
    box.append(el("div", { class: "text" }, `${s.part === "headline" ? "Headline: " : ""}${s.text}`));
    const tags = el("div", { class: "tags" });
    if (s.quoted) tags.append(el("span", { title: "Inside quotation marks: scored as source framing" }, "quoted"));
    for (const [name, [value, evidence]] of Object.entries(s.labels)) {
      tags.append(el("span", { title: evidence }, `${name}: ${value}`));
    }
    box.append(tags);
    for (const g of s.suggestions) {
      const d = el("div", { class: "sugg" });
      d.append(el("div", {}, `Suggestion (Road Collision Reporting Guidelines), not a measured result. ${g.point}: ${g.note}`));
      if (g.rewrite) d.append(el("div", {}, `Suggested: ${g.rewrite}`));
      box.append(d);
    }
    out.append(box);
  }
}

document.getElementById("go").addEventListener("click", async () => {
  out.replaceChildren(el("p", { class: "muted" }, "Labeling…"));
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result }] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: pageText });
    const r = await fetch(SERVER, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
    if (!r.ok) throw new Error(`server returned ${r.status}`);
    render((await r.json()).sentences);
  } catch (e) {
    out.replaceChildren(el("p", { class: "muted" }, `Could not label the page (${e.message}). Is the scoring server running?`));
  }
});
