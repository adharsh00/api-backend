import axios from 'axios'

const backendApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

// ── Custom API ───────────────────────────────────────────────────────────────

/** POST /validate-image — validate an uploaded medical image via the custom API */
export const validateImage = (formData) =>
  backendApi.post('/validate-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

/** GET /formats — list of supported formats from the custom API */
export const getFormats = () => backendApi.get('/formats')

// ── Classmate API (proxied through backend) ───────────────────────────────────

/** GET /appointments/slots — available appointment slots */
export const getSlots = (doctor = '') =>
  backendApi.get('/appointments/slots', { params: doctor ? { doctor } : {} })

/** POST /appointments/reserve — book an appointment slot */
export const reserveSlot = (data) => backendApi.post('/appointments/reserve', data)

/** DELETE /appointments/reserve/:id — cancel a reservation */
export const cancelReservation = (id) => backendApi.delete(`/appointments/reserve/${id}`)

/** GET /appointments/reservations — list all reservations */
export const getReservations = (doctor = '') =>
  backendApi.get('/appointments/reservations', { params: doctor ? { doctor } : {} })

// ── Public API 1 — file.io (called directly from the browser) ────────────────

/** POST https://file.io — upload a file and retrieve its MIME type */
export const detectMime = (formData) => axios.post('https://file.io', formData)

// ── Public API 2 — ClinicalTrials.gov (called directly from the browser) ─────

/** GET https://clinicaltrials.gov/api/v2/studies — search for clinical trials */
export const searchTrials = (condition, pageSize = 5) =>
  axios.get('https://clinicaltrials.gov/api/v2/studies', {
    params: { 'query.cond': condition, pageSize, format: 'json' },
  })
