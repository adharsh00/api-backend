<template>
  <div>
    <!-- Search card ──────────────────────────────────────────────────────── -->
    <div class="card">
      <h2 class="card-title">🔬 Search Clinical Trials</h2>

      <div class="search-row">
        <input
          v-model="query"
          type="text"
          class="form-control"
          placeholder="Enter condition (e.g. medical imaging, radiology, DICOM)"
          @keyup.enter="doSearch"
        />
        <button class="btn btn-primary" :disabled="isSearching" @click="doSearch">
          <span v-if="isSearching" class="spinner"></span>
          {{ isSearching ? 'Searching…' : '🔍 Search' }}
        </button>
      </div>

      <p class="source-note">
        Data provided by
        <strong>ClinicalTrials.gov</strong> — the world's largest registry of
        publicly funded clinical studies. No authentication required.
      </p>
    </div>

    <!-- Error ──────────────────────────────────────────────────────────── -->
    <div v-if="searchError" class="alert alert-danger">⚠️ {{ searchError }}</div>

    <!-- Results ─────────────────────────────────────────────────────────── -->
    <div v-if="studies.length">
      <div class="results-meta">
        <span class="results-label">
          Showing <strong>{{ studies.length }}</strong> results for
          "<em>{{ lastQuery }}</em>"
        </span>
        <span v-if="totalCount" class="results-total">
          {{ totalCount.toLocaleString() }} total studies found
        </span>
      </div>

      <div class="card study-card" v-for="s in studies" :key="nctId(s)">
        <div class="study-header">
          <span class="badge badge-info nct-id">{{ nctId(s) }}</span>
          <span :class="['status-pill', statusClass(overallStatus(s))]">
            {{ overallStatus(s) ?? 'UNKNOWN' }}
          </span>
        </div>

        <h3 class="study-title">{{ briefTitle(s) }}</h3>

        <div class="study-meta">
          <span v-if="phases(s)">📊 {{ phases(s) }}</span>
          <span v-if="sponsor(s)">🏛️ {{ sponsor(s) }}</span>
        </div>

        <p v-if="summary(s)" class="study-summary">{{ truncate(summary(s), 250) }}</p>

        <a
          :href="`https://clinicaltrials.gov/study/${nctId(s)}`"
          target="_blank"
          rel="noopener noreferrer"
          class="view-link"
        >
          View on ClinicalTrials.gov →
        </a>
      </div>
    </div>

    <!-- Empty state ─────────────────────────────────────────────────────── -->
    <div v-else-if="searched && !isSearching" class="card">
      <div class="empty-state">
        <div style="font-size:3rem; margin-bottom:0.5rem;">🔬</div>
        <p>No studies found for "<em>{{ lastQuery }}</em>".</p>
        <p class="empty-hint">Try a broader search term.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchTrials } from '../services/api.js'

const query       = ref('medical imaging')
const studies     = ref([])
const isSearching = ref(false)
const searchError = ref(null)
const totalCount  = ref(null)
const lastQuery   = ref('')
const searched    = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  isSearching.value = true
  searchError.value = null
  lastQuery.value   = query.value
  searched.value    = true

  try {
    const { data } = await searchTrials(query.value, 10)
    studies.value    = data.studies   ?? []
    totalCount.value = data.totalCount ?? null
  } catch (err) {
    searchError.value = err.response?.data?.detail ?? err.message ?? 'Search failed'
    studies.value = []
  } finally {
    isSearching.value = false
  }
}

// ── Data accessors ────────────────────────────────────────────────────────────
const nctId        = (s) => s.protocolSection?.identificationModule?.nctId ?? '—'
const briefTitle   = (s) => s.protocolSection?.identificationModule?.briefTitle ?? 'No title'
const overallStatus= (s) => s.protocolSection?.statusModule?.overallStatus
const phases       = (s) => s.protocolSection?.designModule?.phases?.join(', ')
const sponsor      = (s) => s.protocolSection?.sponsorCollaboratorsModule?.leadSponsor?.name
const summary      = (s) => s.protocolSection?.descriptionModule?.briefSummary

function statusClass(status) {
  const map = {
    RECRUITING:              'pill-recruiting',
    COMPLETED:               'pill-completed',
    ACTIVE_NOT_RECRUITING:   'pill-active',
    NOT_YET_RECRUITING:      'pill-pending',
    TERMINATED:              'pill-stopped',
    WITHDRAWN:               'pill-stopped',
    SUSPENDED:               'pill-stopped',
  }
  return map[status] ?? 'pill-unknown'
}

function truncate(text, max) {
  return text.length > max ? text.slice(0, max) + '…' : text
}
</script>

<style scoped>
/* ── Search row ── */
.search-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
}
.search-row .form-control { flex: 1; min-width: 220px; }
.source-note { font-size: 0.83rem; color: #718096; line-height: 1.5; }

/* ── Results meta ── */
.results-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  font-size: 0.88rem;
  color: #4a5568;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.results-label { font-weight: 600; }
.results-total { color: #718096; }

/* ── Study card ── */
.study-card { padding: 1.25rem 1.5rem; }

.study-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.7rem;
  flex-wrap: wrap;
}
.nct-id { font-family: monospace; font-size: 0.78rem; }

/* Status pills */
.status-pill {
  padding: 0.18rem 0.6rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
}
.pill-recruiting  { background: #c6f6d5; color: #276749; }
.pill-completed   { background: #bee3f8; color: #2b6cb0; }
.pill-active      { background: #fefcbf; color: #744210; }
.pill-pending     { background: #e9d8fd; color: #553c9a; }
.pill-stopped     { background: #fed7d7; color: #c53030; }
.pill-unknown     { background: #e2e8f0; color: #4a5568; }

.study-title {
  font-size: 1rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.study-meta {
  display: flex;
  gap: 1.25rem;
  font-size: 0.8rem;
  color: #718096;
  margin-bottom: 0.65rem;
  flex-wrap: wrap;
}

.study-summary {
  font-size: 0.87rem;
  color: #4a5568;
  line-height: 1.55;
  margin-bottom: 0.75rem;
}

.view-link {
  font-size: 0.84rem;
  color: #2b6cb0;
  text-decoration: none;
  font-weight: 600;
}
.view-link:hover { text-decoration: underline; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 3rem 1rem; color: #718096; }
.empty-hint  { font-size: 0.83rem; margin-top: 0.35rem; }
</style>
