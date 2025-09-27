// Tiny helper
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

const desc = $('#desc');
const wordsEl = $('#words');
const charsEl = $('#chars');

const analyzeBtn = $('#analyze');
const clearAllBtn = $('#clearAll');

const results = $('#results');
const chips = $('#chips');
const loading = $('#loading');
const empty = $('#empty');

let currentFile = null;

// Word & char counter
function updateCounts() {
  const text = desc.value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  wordsEl.textContent = words;
  charsEl.textContent = desc.value.length;
  refreshAnalyzeState();
}

desc.addEventListener('input', updateCounts);
updateCounts();

// Drag & Drop behavior
['dragenter','dragover'].forEach(ev => drop.addEventListener(ev, e => {
  e.preventDefault(); e.stopPropagation();
  drop.classList.add('dragover');
}));
;['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e => {
  e.preventDefault(); e.stopPropagation();
  drop.classList.remove('dragover');
}));

drop.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files?.[0];
  if (file) handleFile(file);
});

browse.addEventListener('click', () => fileInput.click());
replaceBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  if (file) handleFile(file);
});

function handleFile(file) {
  const valid = ['image/png','image/jpeg','image/webp'];
  if (!valid.includes(file.type)) {
    alert('Unsupported file type. Please use PNG, JPG/JPEG, or WebP.');
    return;
  }
  if (file.size > 10 * 1024 * 1024) { // 10MB
    alert('File too large. Please choose an image under 10 MB.');
    return;
  }
  currentFile = file;
  const reader = new FileReader();
  reader.onload = (ev) => {
    thumb.src = ev.target.result;
    preview.style.display = 'grid';
    fname.textContent = file.name;
    fsize.textContent = formatBytes(file.size);
    ftype.textContent = file.type.replace('image/','').toUpperCase();
    refreshAnalyzeState();
  };
  reader.readAsDataURL(file);
}

function formatBytes(bytes) {
  const sizes = ['B','KB','MB','GB'];
  const i = bytes === 0 ? 0 : Math.floor(Math.log(bytes)/Math.log(1024));
  return (bytes/Math.pow(1024,i)).toFixed(i ? 1 : 0) + ' ' + sizes[i];
}

removeBtn.addEventListener('click', () => {
  currentFile = null;
  thumb.removeAttribute('src');
  fileInput.value = '';
  preview.style.display = 'none';
  refreshAnalyzeState();
});

clearAllBtn.addEventListener('click', () => {
  desc.value = '';
  updateCounts();
  currentFile = null;
  fileInput.value = '';
  preview.style.display = 'none';
  showEmptyResults();
  refreshAnalyzeState();
  drop.focus();
});

function refreshAnalyzeState() {
  const hasInput = (desc.value.trim().length > 0) || !!currentFile;
  analyzeBtn.disabled = !hasInput;
  if (!hasInput) showEmptyResults();
}

// Results display (simulated)
analyzeBtn.addEventListener('click', handleAnalyze);

function handleAnalyze() {
  results.hidden = false;
  chips.hidden = true;
  empty.hidden = true;
  loading.style.display = 'block';

  // Simulate network delay
  setTimeout(() => {
    loading.style.display = 'none';
    renderChips(simulateKeywords(desc.value));
  }, 700);
}

function showEmptyResults() {
  results.hidden = false;
  loading.style.display = 'none';
  chips.hidden = true;
  empty.hidden = false;
}

function renderChips(items) {
  chips.replaceChildren();
  if (!items.length) { showEmptyResults(); return; }
  items.forEach(txt => {
    const c = document.createElement('span');
    c.className = 'chip';
    const dot = document.createElement('span');
    dot.className = 'dot';
    const label = document.createElement('span');
    label.textContent = txt;
    c.appendChild(dot);
    c.appendChild(label);
    chips.appendChild(c);
  });
  chips.hidden = false;
}

// Dummy keyword extraction for demo only
function simulateKeywords(text) {
  const base = [
    'handmade', 'artisan', 'custom', 'bespoke', 'minimalist',
    'leather', 'recycled paper', 'engraved', 'A5 journal', 'notebook',
    'gift for writers', 'travel accessory', 'sketchbook', 'refillable', 'eco‑friendly'
  ];
  const extra = (text || '').toLowerCase().match(/[a-z][a-z\- ]{2,}/g) || [];
  const uniq = Array.from(new Set([...extra.map(w => w.trim()), ...base])).filter(Boolean);
  return uniq.slice(0, 18);
}

// Keyboard support for drop area
drop.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput.click();
  }
});

// Initialize
showEmptyResults();

