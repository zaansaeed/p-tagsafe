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
const chips = $('#chips');
const loading = $('#loading');
const empty = $('#empty');

let currentFile = null;
let hasClassified = false;

// Nice Class descriptions mapping
const niceClassDescriptions = {
  '001': 'Chemicals',
  '002': 'Paints',
  '003': 'Cosmetics and cleaning preparations',
  '004': 'Lubricants and fuels',
  '005': 'Pharmaceuticals',
  '006': 'Metal goods',
  '007': 'Machinery',
  '008': 'Hand tools',
  '009': 'Electrical and scientific apparatus',
  '010': 'Medical apparatus',
  '011': 'Environmental control apparatus',
  '012': 'Vehicles',
  '013': 'Firearms',
  '014': 'Jewelry',
  '015': 'Musical instruments',
  '016': 'Paper goods and printed matter',
  '017': 'Rubber goods',
  '018': 'Leather goods',
  '019': 'Non-metallic building materials',
  '020': 'Furniture and articles not otherwise classified',
  '021': 'Housewares and glass',
  '022': 'Cordage and fibers',
  '023': 'Yarns and threads',
  '024': 'Fabrics',
  '025': 'Clothing',
  '026': 'Fancy goods',
  '027': 'Floor coverings',
  '028': 'Toys and sporting goods',
  '029': 'Meats and processed foods',
  '030': 'Staple foods',
  '031': 'Natural agricultural products',
  '032': 'Light beverages',
  '033': 'Wines and spirits',
  '034': 'Smokers articles',
  '035': 'Advertising and business',
  '036': 'Insurance and financial',
  '037': 'Building construction and repair',
  '038': 'Telecommunications',
  '039': 'Transportation and storage',
  '040': 'Treatment of materials',
  '041': 'Education and entertainment',
  '042': 'Computer and scientific',
  '043': 'Hotels and restaurants',
  '044': 'Medical, beauty and agricultural',
  '045': 'Personal'
};

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

// Update class description when Nice Class input changes
niceClass.addEventListener('input', updateClassDescription);

function updateClassDescription() {
  const classNum = niceClass.value.trim().padStart(3, '0');
  const description = niceClassDescriptions[classNum];
  classDescription.textContent = description ? description : '';
}

// Drag & Drop behavior
if (drop) {
  ['dragenter','dragover'].forEach(ev => drop.addEventListener(ev, e => {
    e.preventDefault(); e.stopPropagation();
    drop.classList.add('dragover');
  }));
  ['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e => {
    e.preventDefault(); e.stopPropagation();
    drop.classList.remove('dragover');
  }));

  drop.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  });
}

if (browse) {
  console.log('Browse button found:', browse);
  browse.addEventListener('click', (e) => {
    console.log('Browse clicked!');
    e.preventDefault();
    e.stopPropagation();
    if (fileInput) {
      console.log('Triggering file input:', fileInput);
      fileInput.click();
    }
  });
}
if (replaceBtn) replaceBtn.addEventListener('click', () => fileInput.click());
if (fileInput) {
  console.log('File input found:', fileInput);
  fileInput.addEventListener('change', () => {
    console.log('File input changed!');
    const file = fileInput.files?.[0];
    if (file) handleFile(file);
  });
}

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
    drop.style.display = 'none';
    fname.textContent = file.name;
    fsize.textContent = formatBytes(file.size);
    ftype.textContent = file.type.replace('image/','').toUpperCase();
    classifyBtn.style.display = 'inline-flex';
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
  hasClassified = false;
  thumb.removeAttribute('src');
  fileInput.value = '';
  preview.style.display = 'none';
  drop.style.display = 'grid';
  classifyBtn.style.display = 'none';
  classifyResults.style.display = 'none';
  refreshAnalyzeState();
});

clearAllBtn.addEventListener('click', () => {
  desc.value = '';
  updateCounts();
  currentFile = null;
  hasClassified = false;
  fileInput.value = '';
  preview.style.display = 'none';
  drop.style.display = 'grid';
  classifyBtn.style.display = 'none';
  classifyResults.style.display = 'none';
  niceClass.value = '';
  productText.value = '';
  showEmptyResults();
  refreshAnalyzeState();
  drop.focus();
});

function refreshAnalyzeState() {
  const hasInput = (desc.value.trim().length > 0) || !!currentFile;
  const canAnalyze = hasInput && (!currentFile || hasClassified);
  analyzeBtn.disabled = !canAnalyze;
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

// Classify button handler
classifyBtn.addEventListener('click', handleClassify);

async function handleClassify() {
  if (!currentFile) {
    alert('No image selected');
    return;
  }

  // Show loading state
  classifyBtn.disabled = true;
  classifyBtn.textContent = 'Classifying...';

  try {
    const formData = new FormData();
    formData.append('image', currentFile);

    const response = await fetch('http://127.0.0.1:8000/parser/v1/parse-image', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Extract nice class number from object_type (e.g., "Class 25 – Clothing" -> "025")
    const classMatch = data.result.object_type.match(/Class (\d+)/);
    const classNumber = classMatch ? classMatch[1].padStart(3, '0') : '';
    
    niceClass.value = classNumber;
    productText.value = data.result.text || '';
    classifyResults.style.display = 'grid';
    updateClassDescription();
    hasClassified = true;
    refreshAnalyzeState();
  } catch (error) {
    console.error('Classification error:', error);
    alert('Failed to classify image. Make sure the API is running.');
  } finally {
    classifyBtn.disabled = false;
    classifyBtn.textContent = 'Classify';
  }
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

