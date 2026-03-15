<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">🏥</span>
          <div class="logo-text">
            <h1>MedImage Validator</h1>
            <p>Scalable Cloud-Based Medical Imaging Validation</p>
          </div>
        </div>
        <nav class="nav-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="['nav-btn', activeTab === tab.id ? 'active' : '']"
            @click="activeTab = tab.id"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <UploadImage v-if="activeTab === 'upload'" />
      <Appointments v-if="activeTab === 'appointments'" />
      <ClinicalTrials v-if="activeTab === 'trials'" />
    </main>

    <footer class="app-footer">
      <p>Medical Image Validation Service &mdash; NCI Scalable Cloud Programming CA (H9SCPRO1)</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UploadImage from './components/UploadImage.vue'
import Appointments from './components/Appointments.vue'
import ClinicalTrials from './components/ClinicalTrials.vue'

const activeTab = ref('upload')

const tabs = [
  { id: 'upload',       icon: '🖼️',  label: 'Image Validation' },
  { id: 'appointments', icon: '📅',  label: 'Appointments' },
  { id: 'trials',       icon: '🔬',  label: 'Clinical Trials' },
]
</script>

<style>
/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f0f4f8;
  color: #2d3748;
  min-height: 100vh;
}

#app { min-height: 100vh; display: flex; flex-direction: column; }

/* ── Header ── */
.app-header {
  background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
  color: white;
  padding: 0 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.25);
}
.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0;
  flex-wrap: wrap;
  gap: 1rem;
}
.logo { display: flex; align-items: center; gap: 0.75rem; }
.logo-icon { font-size: 2.5rem; }
.logo-text h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }
.logo-text p  { font-size: 0.78rem; opacity: 0.8; margin-top: 2px; }

/* ── Navigation tabs ── */
.nav-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.15rem;
  border: 2px solid rgba(255,255,255,0.35);
  border-radius: 8px;
  background: rgba(255,255,255,0.1);
  color: white;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.18s;
}
.nav-btn:hover  { background: rgba(255,255,255,0.22); border-color: rgba(255,255,255,0.65); }
.nav-btn.active { background: white; color: #1a365d; border-color: white; }
.tab-icon { font-size: 1rem; }

/* ── Main content area ── */
.app-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 2rem auto;
  padding: 0 1.5rem;
}

/* ── Footer ── */
.app-footer {
  background: #2d3748;
  color: #a0aec0;
  text-align: center;
  padding: 0.9rem;
  font-size: 0.78rem;
}

/* ══ Shared component utilities (consumed by child components) ══ */

.card {
  background: white;
  border-radius: 12px;
  padding: 1.75rem 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  margin-bottom: 1.5rem;
}
.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1a365d;
  margin-bottom: 1.25rem;
  padding-bottom: 0.65rem;
  border-bottom: 2px solid #e2e8f0;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.55rem 1.3rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all 0.18s;
}
.btn-primary { background: #2b6cb0; color: white; }
.btn-primary:hover:not(:disabled) { background: #1a365d; }
.btn-success { background: #38a169; color: white; }
.btn-success:hover:not(:disabled) { background: #276749; }
.btn-danger  { background: #e53e3e; color: white; padding: 0.38rem 0.85rem; font-size: 0.8rem; }
.btn-danger:hover:not(:disabled)  { background: #c53030; }
.btn-secondary { background: #e2e8f0; color: #4a5568; }
.btn-secondary:hover:not(:disabled) { background: #cbd5e0; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }

/* Forms */
.form-group { margin-bottom: 1rem; }
.form-label {
  display: block;
  font-size: 0.82rem;
  font-weight: 700;
  color: #4a5568;
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.form-control {
  width: 100%;
  padding: 0.6rem 0.9rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: white;
  color: #2d3748;
  transition: border-color 0.18s;
}
.form-control:focus { outline: none; border-color: #2b6cb0; }

/* Alerts */
.alert {
  padding: 0.85rem 1.1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.88rem;
  line-height: 1.5;
}
.alert-success { background: #f0fff4; border: 1px solid #9ae6b4; color: #276749; }
.alert-danger  { background: #fff5f5; border: 1px solid #feb2b2; color: #c53030; }
.alert-info    { background: #ebf8ff; border: 1px solid #90cdf4; color: #2c5282; }

/* Badges */
.badge {
  display: inline-block;
  padding: 0.22rem 0.6rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 700;
}
.badge-success { background: #c6f6d5; color: #276749; }
.badge-danger  { background: #fed7d7; color: #c53030; }
.badge-info    { background: #bee3f8; color: #2b6cb0; }

/* Loading spinner */
.spinner {
  display: inline-block;
  width: 0.95rem;
  height: 0.95rem;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Tables */
table { width: 100%; border-collapse: collapse; }
th, td { padding: 0.7rem 1rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
th {
  font-size: 0.75rem;
  font-weight: 700;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f7fafc;
}
tr:hover td { background: #f7fafc; }
</style>
