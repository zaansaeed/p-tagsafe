const $ = (s) => document.querySelector(s);

// Elements
const drop = $('#drop');
const fileInput = $('#file');     
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
const copyBtn = $('#copyBtn');
const tagsContainer = $('#tagsList') || null;

// State
let currentFile = null;
let hasClassified = false;

/* -------------------------------------------------------
   Helper to attach click once
---------------------------------------------------------*/
function attachClickOnce(el, fn) {
  if (!el || el._attached) return;
  el.addEventListener("click", (e) => {
    try { fn(e); } catch (err) { console.error(err); }
  });
  el._attached = true;
}

/* -------------------------------------------------------
   FILE INPUT + BROWSE
---------------------------------------------------------*/

attachClickOnce(browse, (e) => {
  e.preventDefault();
  fileInput.click();
});

if (replaceBtn) {
  replaceBtn.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput.click();
  });
}

// Handle image selection
fileInput.addEventListener("change", () => {
  const f = fileInput.files?.[0];
  if (f) handleFile(f);
});

/* -------------------------------------------------------
   DRAG & DROP
---------------------------------------------------------*/

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
      fileInput.click();
    }
  });
}

/* -------------------------------------------------------
   FILE READING + PREVIEW
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
  const units = ['B','KB','MB','GB'];
  const i = bytes === 0 ? 0 : Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(i ? 1 : 0) + " " + units[i];
}

/* -------------------------------------------------------
   REMOVE IMAGE / CLEAR ALL
---------------------------------------------------------*/

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

/* -------------------------------------------------------
   WORD / CHAR COUNTS
---------------------------------------------------------*/

function updateCounts() {
  const text = desc.value.trim();
  wordsEl.textContent = text ? text.split(/\s+/).length : 0;
  charsEl.textContent = desc.value.length;
  refreshAnalyzeState();
}

desc.addEventListener("input", updateCounts);
updateCounts();

/* -------------------------------------------------------
   ANALYZE BUTTON ENABLE/DISABLE
---------------------------------------------------------*/

function refreshAnalyzeState() {
  const hasInput = desc.value.trim().length > 0 || !!currentFile;
  const canAnalyze = hasInput && (!currentFile || hasClassified);

  analyzeBtn.disabled = !canAnalyze;

  if (!hasInput) showEmptyResults();
}

/* -------------------------------------------------------
   CLASSIFY BUTTON
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
   TEXT OUTPUT + COPY BUTTON (comma separated)
---------------------------------------------------------*/

function clearOutputs() {
  phrasesTextEl.value = "";
  phrasesTextEl.style.display = "none";
  if (copyBtn) copyBtn.style.display = "none";
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
  if (!phrases.length) {
    phrasesTextEl.style.display = "none";
    if (copyBtn) copyBtn.style.display = "none";
    return;
  }

  // Comma-separated list
  phrasesTextEl.value = phrases.join(", ");
  phrasesTextEl.style.display = "block";

  if (copyBtn) copyBtn.style.display = "inline-flex";
}

/* Copy button */
copyBtn.addEventListener("click", () => {
  phrasesTextEl.select();
  phrasesTextEl.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(phrasesTextEl.value).then(() => {
    copyBtn.textContent = "Copied!";
    setTimeout(() => copyBtn.textContent = "Copy", 1200);
  });
});

/* -------------------------------------------------------
   ANALYZE BUTTON — COMPOSE API
---------------------------------------------------------*/

attachClickOnce(analyzeBtn, (e) => {
  e.preventDefault();
  handleAnalyze();
});

async function handleAnalyze() {
  results.hidden = false;
  loading.style.display = "block";
  empty.hidden = true;

  clearOutputs();

  const titleValue = desc.value.trim() || productText.value.trim();
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

    const tags = Array.isArray(data.tags) ? data.tags : [];

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

/* -------------------------------------------------------
   FALLBACK KEYWORDS
---------------------------------------------------------*/

function simulateKeywords(text) {
  const base = [
    "handmade","artisan","custom","minimalist",
    "leather","recycled paper"
  ];

  const extra = (text || "")
    .toLowerCase()
    .match(/[a-z][a-z\- ]{2,}/g) || [];

  const uniq = Array.from(new Set([...extra, ...base]));
  return uniq.slice(0, 18);
}

/* -------------------------------------------------------
   INITIAL
---------------------------------------------------------*/

function showEmptyResults() {
  phrasesTextEl.style.display = "none";
  empty.hidden = false;
}

showEmptyResults();

console.log("script.js (final cleaned) loaded");
