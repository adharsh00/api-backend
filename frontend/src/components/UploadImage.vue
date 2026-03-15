<template>
  <div>
    <!-- Upload card ─────────────────────────────────────────────────────── -->
    <div class="card">
      <h2 class="card-title">📤 Upload Medical Image for Validation</h2>

      <!-- Drop zone -->
      <div
        class="upload-zone"
        :class="{ 'drag-over': isDragging, 'has-file': selectedFile }"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="handleDrop"
        @click="$refs.fileInput.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".dcm,.png,.jpg,.jpeg,.tiff,.tif"
          style="display:none"
          @change="handleFileSelect"
        />

        <div v-if="!selectedFile" class="upload-prompt">
          <div class="upload-icon">📁</div>
          <p class="upload-text">Click to browse or drag &amp; drop a file</p>
          <p class="upload-hint">Accepted: DICOM (.dcm) · PNG · JPEG · TIFF</p>
        </div>

        <div v-else class="file-selected">
          <span class="file-icon">{{ fileIcon }}</span>
          <div class="file-info">
            <p class="file-name">{{ selectedFile.name }}</p>
            <p class="file-size">{{ formatBytes(selectedFile.size) }}</p>
          </div>
          <button class="clear-btn" title="Remove file" @click.stop="clearFile">✕</button>
        </div>
      </div>

      <!-- file.io MIME pre-detection result -->
      <div v-if="mimeResult" class="alert alert-info mime-row">
        <strong>Pre-upload MIME type (file.io):</strong>
        {{ mimeResult.mimeType || 'unknown' }}
        <span v-if="mimeResult.size"> &middot; {{ formatBytes(mimeResult.size) }}</span>
      </div>

      <div v-if="uploadError" class="alert alert-danger">⚠️ {{ uploadError }}</div>

      <div class="btn-row">
        <button
          class="btn btn-primary"
          :disabled="!selectedFile || isValidating"
          @click="validateFile"
        >
          <span v-if="isValidating" class="spinner"></span>
          {{ isValidating ? 'Validating…' : '🔍 Validate Image' }}
        </button>
        <button v-if="selectedFile" class="btn btn-secondary" @click="clearFile">Clear</button>
      </div>
    </div>

    <!-- Validation result card ───────────────────────────────────────────── -->
    <div v-if="validationResult" class="card">
      <h2 class="card-title">📊 Validation Result</h2>

      <div class="result-banner" :class="validationResult.valid ? 'banner-valid' : 'banner-invalid'">
        <span class="banner-icon">{{ validationResult.valid ? '✅' : '❌' }}</span>
        <div>
          <div class="banner-label">{{ validationResult.valid ? 'Valid Format' : 'Invalid Format' }}</div>
          <div class="banner-msg">{{ validationResult.message }}</div>
        </div>
      </div>

      <div class="result-grid">
        <div class="result-tile">
          <div class="tile-label">Format</div>
          <div class="tile-value">
            <span :class="['badge', validationResult.valid ? 'badge-success' : 'badge-danger']">
              {{ validationResult.format }}
            </span>
          </div>
        </div>
        <div class="result-tile">
          <div class="tile-label">File Size</div>
          <div class="tile-value">{{ validationResult.size }}</div>
        </div>
        <div class="result-tile" v-if="validationResult.s3_key">
          <div class="tile-label">S3 Key</div>
          <div class="tile-value mono-sm">{{ validationResult.s3_key }}</div>
        </div>
        <div class="result-tile">
          <div class="tile-label">Validated At</div>
          <div class="tile-value">{{ formatTs(validationResult.timestamp) }}</div>
        </div>
      </div>
    </div>

    <!-- Info card ────────────────────────────────────────────────────────── -->
    <div class="card">
      <h2 class="card-title">ℹ️ About This Service</h2>
      <p class="info-body">
        Files are stored securely in <strong>Amazon S3</strong> and processed
        asynchronously via <strong>AWS SQS</strong>. A MIME pre-check is performed
        using <strong>file.io</strong> before the image reaches the validation API.
      </p>
      <div class="chip-row">
        <span v-for="f in ['DICOM', 'PNG', 'JPEG', 'TIFF']" :key="f" class="chip">{{ f }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { validateImage, detectMime } from '../services/api.js'

const selectedFile  = ref(null)
const isDragging    = ref(false)
const isValidating  = ref(false)
const validationResult = ref(null)
const mimeResult    = ref(null)
const uploadError   = ref(null)

const fileIcon = computed(() => {
  if (!selectedFile.value) return '📄'
  const ext = selectedFile.value.name.split('.').pop().toLowerCase()
  return { dcm: '🏥', png: '🖼️', jpg: '🖼️', jpeg: '🖼️', tif: '🖼️', tiff: '🖼️' }[ext] ?? '📄'
})

// ── Event handlers ──────────────────────────────────────────────────────────

function handleFileSelect(e) {
  const f = e.target.files[0]
  if (f) setFile(f)
}

function handleDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) setFile(f)
}

function setFile(file) {
  selectedFile.value = file
  validationResult.value = null
  mimeResult.value = null
  uploadError.value = null
  prefetchMime(file)
}

function clearFile() {
  selectedFile.value = null
  validationResult.value = null
  mimeResult.value = null
  uploadError.value = null
}

// ── API calls ───────────────────────────────────────────────────────────────

async function prefetchMime(file) {
  try {
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await detectMime(fd)
    if (data?.success) mimeResult.value = data
  } catch {
    // file.io detection is best-effort; silently ignore failures
  }
}

async function validateFile() {
  if (!selectedFile.value) return
  isValidating.value = true
  uploadError.value = null
  validationResult.value = null

  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    const { data } = await validateImage(fd)
    validationResult.value = data
  } catch (err) {
    uploadError.value =
      err.response?.data?.detail ?? err.message ?? 'Validation failed. Please try again.'
  } finally {
    isValidating.value = false
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatBytes(n) {
  if (n < 1024)        return `${n} B`
  if (n < 1024 ** 2)  return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 ** 2).toFixed(2)} MB`
}

function formatTs(ts) {
  return new Date(ts).toLocaleString()
}
</script>

<style scoped>
/* ── Drop zone ── */
.upload-zone {
  border: 2px dashed #cbd5e0;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f7fafc;
  margin-bottom: 1rem;
}
.upload-zone:hover,
.upload-zone.drag-over { border-color: #2b6cb0; background: #ebf8ff; }
.upload-zone.has-file  { border-style: solid; border-color: #4299e1; }

.upload-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.upload-text { font-size: 1.05rem; font-weight: 600; color: #2d3748; }
.upload-hint { font-size: 0.82rem; color: #718096; margin-top: 0.25rem; }

.file-selected { display: flex; align-items: center; gap: 1rem; text-align: left; }
.file-icon  { font-size: 2.5rem; flex-shrink: 0; }
.file-info  { flex: 1; min-width: 0; }
.file-name  { font-weight: 600; color: #2d3748; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-size  { font-size: 0.82rem; color: #718096; }
.clear-btn  { background: none; border: none; font-size: 1.15rem; cursor: pointer; color: #a0aec0; padding: 0.25rem; transition: color 0.15s; flex-shrink: 0; }
.clear-btn:hover { color: #e53e3e; }

/* ── MIME row ── */
.mime-row { margin-bottom: 1rem; }

/* ── Button row ── */
.btn-row { display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap; }

/* ── Result banner ── */
.result-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border-radius: 10px;
  margin-bottom: 1.25rem;
}
.banner-valid   { background: #f0fff4; border: 1px solid #9ae6b4; }
.banner-invalid { background: #fff5f5; border: 1px solid #feb2b2; }
.banner-icon    { font-size: 2.25rem; flex-shrink: 0; }
.banner-label   { font-size: 1.05rem; font-weight: 700; }
.banner-msg     { font-size: 0.88rem; color: #4a5568; margin-top: 2px; }

/* ── Result grid ── */
.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 0.9rem; }
.result-tile { padding: 0.8rem 1rem; background: #f7fafc; border-radius: 8px; }
.tile-label  { font-size: 0.72rem; font-weight: 700; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
.tile-value  { font-size: 0.92rem; font-weight: 600; color: #2d3748; word-break: break-all; }
.mono-sm     { font-family: monospace; font-size: 0.73rem; }

/* ── Info card ── */
.info-body { color: #4a5568; line-height: 1.65; margin-bottom: 1rem; font-size: 0.9rem; }
.chip-row  { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.chip {
  padding: 0.28rem 0.75rem;
  background: #ebf8ff;
  color: #2b6cb0;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 700;
}
</style>
