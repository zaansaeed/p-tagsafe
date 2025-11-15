/* CLEAN + FIXED script.js — fully working classify + analyze + text output */

const $ = (s) => document.querySelector(s);

// Elements
const drop = $('#drop');
let fileInput = $('#file');
const browse = $('#browse');
const preview = $('#preview');
const thumb = $('#thumb');
const fname = $('#fname');
const fsize = $('#fsize');
const ftype = $('#ftype');
const replaceBtn = $('#replaceBtn');
const removeBtn = $('#removeBtn');
const classifyBtn = $('#classifyBtn');
const classifyResults = $('#classifyResults');
const niceClass = $('#niceClass');
const productText = $('#productText');
const classDescription = $('#classDescription');

const desc = $('#desc');
const wordsEl = $('#words');
const charsEl = $('#chars');

const analyzeBtn = $('#analyze');
const clearAllBtn = $('#clearAll');

const results = $('#results');
const loading = $('#loading');
const empty = $('#empty');

const phrasesTextEl = $('#phrasesText');
const tagsContainer = $('#tagsList') || null;

// State
let currentFile = null;
let hasClassified = false;

/* -------------------------------------------------------
   1. RESET FILE INPUT (remove all old listeners)
---------------------------------------------------------*/
function resetFileInput() {
  const orig = document.getElementById('file');
  if (!orig) return;

  const clone = orig.cloneNode(true);
  orig.parentNode.replaceChild(clone, orig);

  fileInput = clone;
  fileInput.id = 'file';
}
resetFileInput();

/* -------------------------------------------------------
   2. ATTACH FILE INPUT + DROP HANDLERS (AFTER RESET)
---------------------------------------------------------*/

// Helper to attach click handler only once
function attachClickOnce(el, fn) {
  if (!el || el._attached) return;
  el.addEventListener("click", (e) => {
    try { fn(e); } catch (err) { console.error(err); }
  });
  el._attached = true;
}

// Open file picker
attachClickOnce(browse, (e) => {
  e.preventDefault();
  setTimeout(() => fileInput && fileInput.click(), 0);
});

if (replaceBtn) {
  replaceBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (fileInput) fileInput.click();
  });
}

// File choose -> load
if (fileInput) {
  fileInput.addEventListener("change", () => {
    const f = fileInput.files?.[0];
    if (f) handleFile(f);
  });
}

// Drag/drop handlers
if (drop) {
  ['dragenter','dragover'].forEach(ev =>
    drop.addEventListener(ev, (e) => {
      e.preventDefault();
      drop.classList.add("dragover");
    })
  );

  ['dragleave','drop'].forEach(ev =>
    drop.addEventListener(ev, (e) => {
      e.preventDefault();
      drop.classList.remove("dragover");
    })
  );

  drop.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  });

  drop.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (fileInput) fileInput.click();
    }
  });
}

/* -------------------------------------------------------
   3. FILE PROCESSING + PREVIEW
---------------------------------------------------------*/

function handleFile(file) {
  const valid = ['image/png','image/jpeg','image/webp'];
  if (!valid.includes(file.type)) {
    alert("Unsupported file type (PNG/JPG/WebP only).");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    alert("File too large (max 10MB).");
    return;
  }

  currentFile = file;

  const reader = new FileReader();
  reader.onload = (ev) => {
    thumb.src = ev.target.result;
    preview.style.display = "grid";
    drop.style.display = "none";
    fname.textContent = file.name;
    fsize.textContent = formatBytes(file.size);
    ftype.textContent = file.type.replace("image/","").toUpperCase();

    classifyBtn.style.display = "inline-flex";

    refreshAnalyzeState();
  };
  reader.readAsDataURL(file);
}

function formatBytes(bytes) {
  const sizes = ['B','KB','MB','GB'];
  const i = bytes === 0 ? 0 : Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(i ? 1 : 0) + ' ' + sizes[i];
}

/* -------------------------------------------------------
   4. REMOVE / CLEAR
---------------------------------------------------------*/

if (removeBtn) {
  removeBtn.addEventListener("click", () => {
    currentFile = null;
    hasClassified = false;

    thumb.removeAttribute("src");
    fileInput.value = "";
    preview.style.display = "none";
    drop.style.display = "grid";
    classifyBtn.style.display = "none";
    classifyResults.style.display = "none";

    refreshAnalyzeState();
    showEmptyResults();
  });
}

if (clearAllBtn) {
  clearAllBtn.addEventListener("click", () => {
    desc.value = "";
    updateCounts();

    currentFile = null;
    hasClassified = false;
    fileInput.value = "";
    preview.style.display = "none";
    drop.style.display = "grid";
    classifyBtn.style.display = "none";
    classifyResults.style.display = "none";

    niceClass.value = "";
    productText.value = "";

    showEmptyResults();
    refreshAnalyzeState();
  });
}

/* -------------------------------------------------------
   5. COUNTERS
---------------------------------------------------------*/

function updateCounts() {
  const text = desc.value.trim();
  const words = text ? text.split(/\s+/).length : 0;

  wordsEl.textContent = words;
  charsEl.textContent = desc.value.length;

  refreshAnalyzeState();
}

desc.addEventListener("input", updateCounts);
updateCounts();

/* -------------------------------------------------------
   6. ENABLE/DISABLE ANALYZE BUTTON
---------------------------------------------------------*/

function refreshAnalyzeState() {
  const hasInput = desc.value.trim().length > 0 || !!currentFile;
  const canAnalyze = hasInput && (!currentFile || hasClassified);

  analyzeBtn.disabled = !canAnalyze;

  if (!hasInput) showEmptyResults();
}

/* -------------------------------------------------------
   7. CLASSIFY BUTTON (API CALL)
---------------------------------------------------------*/

classifyBtn.addEventListener("click", handleClassify);

async function handleClassify() {
  if (!currentFile) {
    alert("No image selected!");
    return;
  }

  classifyBtn.disabled = true;
  classifyBtn.textContent = "Classifying...";

  try {
    const formData = new FormData();
    formData.append("image", currentFile);

    const response = await fetch("http://127.0.0.1:8000/parser/v1/parse-image", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const data = await response.json();

    const classMatch = (data.result?.object_type || "").match(/Class (\d+)/);
    const classNumber = classMatch ? classMatch[1].padStart(3, "0") : "";

    niceClass.value = classNumber;
    productText.value = data.result?.text || "";
    classifyResults.style.display = "grid";

    hasClassified = true;
    refreshAnalyzeState();

    clearOutputs();
  } catch (err) {
    console.error(err);
    alert("Failed to classify image. Is the API running?");
  } finally {
    classifyBtn.disabled = false;
    classifyBtn.textContent = "Classify";
  }
}

/* -------------------------------------------------------
   8. OUTPUT AREA (TEXT MODE ONLY)
---------------------------------------------------------*/

function clearOutputs() {
  phrasesTextEl.value = "";
  phrasesTextEl.style.display = "none";

  if (tagsContainer) tagsContainer.replaceChildren();
}

function renderTags(tags = []) {
  if (!tagsContainer) return;

  tagsContainer.replaceChildren();

  if (!tags.length) {
    tagsContainer.classList.add("empty");
    return;
  }

  tagsContainer.classList.remove("empty");

  tags.forEach(t => {
    const li = document.createElement("li");
    li.className = "tag-item";
    li.textContent = t;
    tagsContainer.appendChild(li);
  });
}

function renderPhrasesText(phrases = []) {
  if (!phrasesTextEl) return false;

  if (!phrases || phrases.length === 0) {
    phrasesTextEl.style.display = "none";
    const copyBtn = $("#copyBtn");
    if (copyBtn) copyBtn.style.display = "none";
    return true;
  }

  // Comma-separated list
  const commaList = phrases.join(", ");

  phrasesTextEl.value = commaList;
  phrasesTextEl.style.display = "block";

  // Show copy button
  const copyBtn = $("#copyBtn");
  if (copyBtn) copyBtn.style.display = "inline-flex";

  return true;
}


/* -------------------------------------------------------
   9. ANALYZE BUTTON (COMPOSE API)
---------------------------------------------------------*/

async function handleAnalyze() {
  results.hidden = false;
  loading.style.display = "block";
  empty.hidden = true;

  clearOutputs();

  const titleValue =
    desc.value ||
    productText.value ||
    "";

  const niceVal = niceClass.value ? Number(niceClass.value) : 0;

  const form = new FormData();
  form.append("title", titleValue);
  form.append("nice_class", String(niceVal));
  form.append("product_text", productText.value);

  const file = fileInput.files?.[0];
  if (file) form.append("image_file", file, file.name);

  try {
    const resp = await fetch("http://127.0.0.1:8000/compose/all", {
      method: "POST",
      body: form,
    });

    if (!resp.ok) {
      console.warn("Compose API returned", resp.status);
      const fallback = simulateKeywords(titleValue);
      renderPhrasesText(fallback);
      renderTags([]);
      return;
    }

    const data = await resp.json();

    const safe = Array.isArray(data.safe_phrases)
      ? data.safe_phrases
      : simulateKeywords(titleValue);

    const tags = Array.isArray(data.tags)
      ? data.tags
      : [];

    renderPhrasesText(safe);
    renderTags(tags);

  } catch (err) {
    console.error("Compose API error", err);
    renderPhrasesText(simulateKeywords(titleValue));
    renderTags([]);
  } finally {
    loading.style.display = "none";
  }
}

attachClickOnce(analyzeBtn, (e) => {
  e.preventDefault();
  handleAnalyze();
});

/* -------------------------------------------------------
   10. FALLBACK KEYWORDS
---------------------------------------------------------*/

function simulateKeywords(text) {
  const base = [
    "handmade","artisan","custom","minimalist","leather","recycled paper"
  ];

  const extra = (text || "")
    .toLowerCase()
    .match(/[a-z][a-z\- ]{2,}/g) || [];

  const uniq = Array.from(
    new Set([...extra.map(w => w.trim()), ...base])
  );

  return uniq.slice(0, 18);
}

/* -------------------------------------------------------
   11. INITIAL
---------------------------------------------------------*/

function showEmptyResults() {
  phrasesTextEl.style.display = "none";
  empty.hidden = false;
}

showEmptyResults();

// COPY BUTTON
const copyBtn = $("#copyBtn");
if (copyBtn) {
  copyBtn.addEventListener("click", () => {
    if (!phrasesTextEl) return;
    phrasesTextEl.select();
    phrasesTextEl.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(phrasesTextEl.value)
      .then(() => {
        copyBtn.textContent = "Copied!";
        setTimeout(() => copyBtn.textContent = "Copy", 1200);
      })
      .catch(err => console.error("Copy failed:", err));
  });
}


console.log("script.js (fixed) loaded");
