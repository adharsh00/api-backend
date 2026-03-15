<template>
  <div>
    <!-- Available Slots ───────────────────────────────────────────────────── -->
    <div class="card">
      <h2 class="card-title">📅 Available Appointment Slots</h2>

      <div class="filter-row">
        <input
          v-model="doctorFilter"
          type="text"
          class="form-control filter-input"
          placeholder="Filter by doctor (e.g. Dr Smith)"
          @keyup.enter="fetchSlots"
        />
        <button class="btn btn-primary" :disabled="isLoadingSlots" @click="fetchSlots">
          <span v-if="isLoadingSlots" class="spinner"></span>
          {{ isLoadingSlots ? 'Loading…' : '🔄 Refresh' }}
        </button>
      </div>

      <div v-if="slotsError" class="alert alert-danger">⚠️ {{ slotsError }}</div>

      <div v-if="slots.length" class="slots-grid">
        <div
          v-for="slot in slots"
          :key="`${slot.doctor}-${slot.time}`"
          :class="['slot-card', slot.available ? 'slot-avail' : 'slot-booked']"
        >
          <div class="slot-time">{{ slot.time }}</div>
          <div class="slot-doctor">{{ slot.doctor }}</div>
          <span :class="['badge', slot.available ? 'badge-success' : 'badge-danger']">
            {{ slot.available ? 'Available' : 'Booked' }}
          </span>
          <button
            v-if="slot.available"
            class="btn btn-success slot-book-btn"
            @click="prefillForm(slot)"
          >
            Book
          </button>
        </div>
      </div>
      <div v-else-if="!isLoadingSlots" class="empty-state">
        No slots found.
        <a href="#" @click.prevent="fetchSlots">Click to load.</a>
      </div>
    </div>

    <!-- Book Appointment ─────────────────────────────────────────────────── -->
    <div class="card">
      <h2 class="card-title">✏️ Book an Appointment</h2>

      <div class="form-grid">
        <div class="form-group">
          <label class="form-label">Patient Name *</label>
          <input v-model="form.patient_name" type="text" class="form-control" placeholder="John Doe" />
        </div>
        <div class="form-group">
          <label class="form-label">Doctor *</label>
          <input v-model="form.doctor" type="text" class="form-control" placeholder="Dr Smith" />
        </div>
        <div class="form-group">
          <label class="form-label">Time *</label>
          <input v-model="form.time" type="text" class="form-control" placeholder="10:00" />
        </div>
      </div>

      <div v-if="bookingError"   class="alert alert-danger">⚠️ {{ bookingError }}</div>
      <div v-if="bookingSuccess" class="alert alert-success">{{ bookingSuccess }}</div>

      <button
        class="btn btn-primary"
        :disabled="isBooking || !form.patient_name || !form.doctor || !form.time"
        @click="bookAppointment"
      >
        <span v-if="isBooking" class="spinner"></span>
        {{ isBooking ? 'Booking…' : '📋 Book Appointment' }}
      </button>
    </div>

    <!-- My Reservations ──────────────────────────────────────────────────── -->
    <div class="card">
      <div class="section-header">
        <h2 class="card-title" style="margin-bottom:0; border-bottom:none; padding-bottom:0;">
          📋 My Reservations
        </h2>
        <button
          class="btn btn-primary"
          style="font-size:0.8rem; padding:0.38rem 0.85rem;"
          :disabled="isLoadingReservations"
          @click="fetchReservations"
        >
          <span v-if="isLoadingReservations" class="spinner"></span>
          {{ isLoadingReservations ? '' : '🔄 Refresh' }}
        </button>
      </div>
      <div class="divider"></div>

      <div v-if="reservationsError" class="alert alert-danger">⚠️ {{ reservationsError }}</div>
      <div v-if="cancelSuccess"     class="alert alert-success">{{ cancelSuccess }}</div>

      <div v-if="reservations.length" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Reservation ID</th>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Time</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reservations" :key="r.reservation_id">
              <td class="mono">{{ r.reservation_id }}</td>
              <td>{{ r.patient_name }}</td>
              <td>{{ r.doctor }}</td>
              <td>{{ r.time }}</td>
              <td>
                <button
                  class="btn btn-danger"
                  :disabled="cancellingId === r.reservation_id"
                  @click="cancelBooking(r.reservation_id)"
                >
                  {{ cancellingId === r.reservation_id ? '…' : 'Cancel' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else-if="!isLoadingReservations" class="empty-state">
        No reservations found.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getSlots,
  reserveSlot,
  cancelReservation,
  getReservations,
} from '../services/api.js'

// ── State ────────────────────────────────────────────────────────────────────
const slots        = ref([])
const reservations = ref([])
const doctorFilter = ref('')

const form = ref({ patient_name: '', doctor: '', time: '' })

const isLoadingSlots        = ref(false)
const isLoadingReservations = ref(false)
const isBooking             = ref(false)
const cancellingId          = ref(null)

const slotsError        = ref(null)
const bookingError      = ref(null)
const bookingSuccess    = ref(null)
const reservationsError = ref(null)
const cancelSuccess     = ref(null)

// ── API calls ─────────────────────────────────────────────────────────────────
async function fetchSlots() {
  isLoadingSlots.value = true
  slotsError.value = null
  try {
    const { data } = await getSlots(doctorFilter.value)
    slots.value = data.slots ?? []
  } catch (err) {
    slotsError.value = err.response?.data?.detail ?? err.message ?? 'Failed to load slots'
  } finally {
    isLoadingSlots.value = false
  }
}

async function fetchReservations() {
  isLoadingReservations.value = true
  reservationsError.value = null
  try {
    const { data } = await getReservations()
    reservations.value = data.reservations ?? []
  } catch (err) {
    reservationsError.value = err.response?.data?.detail ?? err.message ?? 'Failed to load reservations'
  } finally {
    isLoadingReservations.value = false
  }
}

function prefillForm(slot) {
  form.value.doctor = slot.doctor
  form.value.time   = slot.time
  // Scroll user down to the booking form
  document.querySelector('.card:nth-child(2)')?.scrollIntoView({ behavior: 'smooth' })
}

async function bookAppointment() {
  isBooking.value    = true
  bookingError.value = null
  bookingSuccess.value = null
  try {
    const { data } = await reserveSlot(form.value)
    bookingSuccess.value = `✅ ${data.message} — Reservation ID: ${data.reservation_id}`
    form.value = { patient_name: '', doctor: '', time: '' }
    fetchReservations()
    fetchSlots()
  } catch (err) {
    bookingError.value = err.response?.data?.detail ?? err.message ?? 'Booking failed'
  } finally {
    isBooking.value = false
  }
}

async function cancelBooking(id) {
  cancellingId.value  = id
  cancelSuccess.value = null
  reservationsError.value = null
  try {
    await cancelReservation(id)
    cancelSuccess.value = `✅ Reservation ${id} cancelled.`
    fetchReservations()
    fetchSlots()
  } catch (err) {
    reservationsError.value = err.response?.data?.detail ?? err.message ?? 'Cancellation failed'
  } finally {
    cancellingId.value = null
  }
}

onMounted(() => {
  fetchSlots()
  fetchReservations()
})
</script>

<style scoped>
/* ── Slots ── */
.filter-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  align-items: center;
}
.filter-input { flex: 1; min-width: 200px; max-width: 350px; }

.slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.9rem;
}
.slot-card {
  padding: 1rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  text-align: center;
  transition: transform 0.1s;
}
.slot-card:hover    { transform: translateY(-2px); }
.slot-avail         { background: #f0fff4; border-color: #9ae6b4; }
.slot-booked        { background: #f7fafc; opacity: 0.65; }
.slot-time   { font-size: 1.45rem; font-weight: 700; color: #2d3748; margin-bottom: 0.2rem; }
.slot-doctor { font-size: 0.82rem; color: #718096; margin-bottom: 0.5rem; }
.slot-book-btn { margin-top: 0.55rem; padding: 0.35rem 0.9rem; font-size: 0.8rem; }

/* ── Booking form ── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

/* ── Reservations ── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.divider { border-bottom: 2px solid #e2e8f0; margin: 0.5rem 0 1.25rem; }
.table-wrap { overflow-x: auto; }
.mono { font-family: monospace; font-size: 0.78rem; }

.empty-state { text-align: center; padding: 2rem; color: #718096; }
.empty-state a { color: #2b6cb0; }
</style>
