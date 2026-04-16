<template>
  <div>

    <!-- ── Header ──────────────────────────────────────────────────────────── -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-800">Dashboard</h1>
      <div class="flex gap-3">
        <button
          @click="connectBank"
          :disabled="connecting"
          class="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          {{ connecting ? 'Connecting…' : 'Connect SEB' }}
        </button>
        <button
          @click="syncTransactions"
          :disabled="syncing"
          class="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': syncing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ syncing ? 'Syncing…' : 'Sync Transactions' }}
        </button>
      </div>
    </div>

    <!-- ── Feedback banner ─────────────────────────────────────────────────── -->
    <transition name="fade">
      <div
        v-if="message"
        :class="messageType === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'"
        class="mb-6 px-4 py-3 rounded-lg border text-sm font-medium flex justify-between items-center"
      >
        <span>{{ message }}</span>
        <button @click="message = ''" class="ml-4 opacity-60 hover:opacity-100 text-lg leading-none">&times;</button>
      </div>
    </transition>

    <!-- ── Empty state ─────────────────────────────────────────────────────── -->
    <div v-if="transactions.length === 0" class="bg-white rounded-xl border border-gray-100 shadow-sm py-20 text-center">
      <p class="text-gray-400">No data yet.</p>
      <p class="text-gray-400 text-sm mt-1">Connect your SEB account and click <strong>Sync Transactions</strong>.</p>
    </div>

    <template v-else>

      <!-- ── Month selector ────────────────────────────────────────────────── -->
      <div class="flex gap-3 overflow-x-auto pb-3 mb-6 scrollbar-hide" ref="monthScroller">
        <button
          v-for="m in monthlySummaries"
          :key="m.key"
          :data-month="m.key"
          @click="selectedMonth = m.key"
          :class="selectedMonth === m.key
            ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
            : 'bg-white text-gray-700 border-gray-200 hover:border-indigo-300 hover:shadow-sm'"
          class="flex-shrink-0 border rounded-xl px-5 py-3 text-left transition-all duration-150 cursor-pointer w-36"
        >
          <p class="text-sm font-bold leading-tight">{{ m.shortMonth }}</p>
          <p :class="selectedMonth === m.key ? 'text-indigo-200' : 'text-gray-400'" class="text-xs mb-2">
            {{ m.year }}
          </p>
          <p
            class="text-base font-bold"
            :class="selectedMonth === m.key
              ? (m.net >= 0 ? 'text-green-300' : 'text-red-300')
              : (m.net >= 0 ? 'text-green-600' : 'text-red-500')"
          >
            {{ m.net >= 0 ? '+' : '−' }}{{ compactSEK(m.net) }}
          </p>
        </button>
      </div>

      <!-- ── Month label ───────────────────────────────────────────────────── -->
      <h2 class="text-xl font-bold text-gray-700 mb-4">{{ selectedMonthLabel }}</h2>

      <!-- ── Summary cards ─────────────────────────────────────────────────── -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p class="text-xs text-gray-400 uppercase font-semibold tracking-wide">Income</p>
          <p class="text-3xl font-bold text-green-600 mt-2">+{{ formatSEK(selectedIncome) }}</p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p class="text-xs text-gray-400 uppercase font-semibold tracking-wide">Expenses</p>
          <p class="text-3xl font-bold text-red-500 mt-2">−{{ formatSEK(selectedExpenses) }}</p>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p class="text-xs text-gray-400 uppercase font-semibold tracking-wide">Net</p>
          <p
            class="text-3xl font-bold mt-2"
            :class="selectedNet >= 0 ? 'text-indigo-600' : 'text-red-600'"
          >
            {{ selectedNet >= 0 ? '+' : '−' }}{{ formatSEK(selectedNet) }}
          </p>
        </div>
      </div>

      <!-- ── Charts ────────────────────────────────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Spending by category (selected month) -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 class="text-base font-semibold text-gray-700 mb-4">Spending by Category</h3>
          <div class="h-64 flex justify-center">
            <Pie v-if="hasExpenses" :data="pieChartData" :options="pieOptions" />
            <p v-else class="text-gray-400 text-sm self-center">No expenses this month</p>
          </div>
        </div>

        <!-- Monthly overview (all months, selected one highlighted) -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 class="text-base font-semibold text-gray-700 mb-4">Monthly Overview</h3>
          <div class="h-64">
            <Bar :data="barChartData" :options="barOptions" />
          </div>
        </div>

      </div>

      <!-- ── Transactions for selected month ──────────────────────────────── -->
      <h3 class="text-base font-semibold text-gray-700 mt-8 mb-3">
        Transactions — {{ selectedMonthLabel }}
      </h3>

      <div class="space-y-2">
        <div
          v-for="cat in selectedCategories"
          :key="cat.name"
          class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <!-- Category header row -->
          <button
            @click="toggleCategory(cat.name)"
            class="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors text-left"
          >
            <div class="flex items-center gap-3">
              <svg
                class="w-4 h-4 text-gray-400 transition-transform"
                :class="{ 'rotate-90': openCategories.has(cat.name) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <span class="text-sm font-semibold text-gray-800">{{ cat.name }}</span>
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                {{ cat.transactions.length }} {{ cat.transactions.length === 1 ? 'transaction' : 'transactions' }}
              </span>
            </div>
            <span class="text-sm font-bold" :class="cat.total >= 0 ? 'text-green-600' : 'text-red-500'">
              {{ cat.total >= 0 ? '+' : '−' }}{{ formatSEK(cat.total) }}
            </span>
          </button>

          <!-- Expanded rows -->
          <div v-if="openCategories.has(cat.name)" class="border-t border-gray-50">
            <div
              v-for="t in cat.transactions"
              :key="t.id"
              class="flex items-center justify-between px-5 py-2.5 hover:bg-gray-50 border-b border-gray-50 last:border-0 transition-colors"
            >
              <div class="flex items-center gap-4 min-w-0">
                <span class="text-xs text-gray-400 w-14 shrink-0">{{ formatDate(t.date) }}</span>
                <span class="text-sm text-gray-500 truncate">{{ t.note || t.category }}</span>
              </div>
              <span class="text-sm font-medium shrink-0" :class="t.type === 'income' ? 'text-green-600' : 'text-red-500'">
                {{ t.type === 'income' ? '+' : '−' }}{{ formatSEK(t.amount) }}
              </span>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script>
import axios from 'axios'
import { Pie, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  BarElement, CategoryScale, LinearScale,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const COLORS = ['#4f46e5','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#f97316']

export default {
  components: { Pie, Bar },

  data() {
    return {
      transactions: [],
      selectedMonth: null,   // "2025-04"
      syncing: false,
      connecting: false,
      message: '',
      messageType: 'success',
      openCategories: new Set(),
      pieOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } } },
      },
      barOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
        scales: { x: { grid: { display: false } }, y: { grid: { color: '#f3f4f6' } } },
      },
    }
  },

  computed: {
    // ── Per-month summaries for the selector row ────────────────────────────
    monthlySummaries() {
      const map = {}
      for (const t of this.transactions) {
        const key = t.date.substring(0, 7)
        if (!map[key]) map[key] = { income: 0, expenses: 0 }
        if (t.type === 'income') map[key].income += t.amount
        else map[key].expenses += t.amount
      }
      return Object.keys(map)
        .sort((a, b) => b.localeCompare(a))   // newest first
        .map(key => {
          const [year, mon] = key.split('-')
          const d = new Date(year, mon - 1)
          return {
            key,
            shortMonth: d.toLocaleString('en-US', { month: 'short' }),
            year,
            income:   map[key].income,
            expenses: map[key].expenses,
            net:      map[key].income - map[key].expenses,
          }
        })
    },

    selectedMonthLabel() {
      if (!this.selectedMonth) return ''
      const [y, m] = this.selectedMonth.split('-')
      return new Date(y, m - 1).toLocaleString('en-US', { month: 'long', year: 'numeric' })
    },

    // ── Transactions for selected month ─────────────────────────────────────
    selectedTxs() {
      if (!this.selectedMonth) return []
      return this.transactions.filter(t => t.date.startsWith(this.selectedMonth))
    },

    selectedIncome() {
      return this.selectedTxs.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0)
    },
    selectedExpenses() {
      return this.selectedTxs.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0)
    },
    selectedNet() {
      return this.selectedIncome - this.selectedExpenses
    },

    hasExpenses() {
      return this.selectedTxs.some(t => t.type === 'expense')
    },

    // ── Pie: top 8 expense categories for selected month ────────────────────
    pieChartData() {
      const catMap = {}
      for (const t of this.selectedTxs.filter(t => t.type === 'expense')) {
        catMap[t.category] = (catMap[t.category] || 0) + t.amount
      }
      const sorted = Object.entries(catMap)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 8)
      return {
        labels: sorted.map(([k]) => k),
        datasets: [{
          data: sorted.map(([, v]) => v),
          backgroundColor: COLORS,
          borderWidth: 0,
        }],
      }
    },

    // ── Transactions for selected month grouped by category ─────────────────
    selectedCategories() {
      const catMap = {}
      for (const t of this.selectedTxs) {
        const name = t.category || 'Other'
        if (!catMap[name]) catMap[name] = []
        catMap[name].push(t)
      }
      return Object.keys(catMap)
        .map(name => {
          const txs = [...catMap[name]].sort((a, b) => b.date.localeCompare(a.date))
          const total = txs.reduce((s, t) => t.type === 'income' ? s + t.amount : s - t.amount, 0)
          return { name, transactions: txs, total }
        })
        .sort((a, b) => a.total - b.total)  // biggest expenses first, income last
    },

    // ── Bar: all months, selected month highlighted ──────────────────────────
    barChartData() {
      const all = [...this.monthlySummaries].reverse()  // oldest → newest (left → right)
      return {
        labels: all.map(m => `${m.shortMonth} ${m.year.slice(2)}`),
        datasets: [
          {
            label: 'Income',
            data: all.map(m => m.income),
            backgroundColor: all.map(m => m.key === this.selectedMonth ? '#059669' : '#d1fae5'),
            borderRadius: 4,
          },
          {
            label: 'Expenses',
            data: all.map(m => m.expenses),
            backgroundColor: all.map(m => m.key === this.selectedMonth ? '#dc2626' : '#fee2e2'),
            borderRadius: 4,
          },
        ],
      }
    },
  },

  watch: {
    // Auto-select the most recent month once data loads
    monthlySummaries(summaries) {
      if (!this.selectedMonth && summaries.length > 0) {
        this.selectedMonth = summaries[0].key
      }
    },

    // Reset open categories when switching months
    selectedMonth() {
      this.openCategories = new Set()
    },

    // Scroll the selected month card into view
    selectedMonth(key) {
      this.$nextTick(() => {
        const el = this.$refs.monthScroller?.querySelector(`[data-month="${key}"]`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      })
    },
  },

  mounted() {
    this.fetchTransactions()
    const params = new URLSearchParams(window.location.search)
    if (params.get('sync') === 'success') {
      this.showMessage('SEB connected! Click "Sync Transactions" to import your data.')
      window.history.replaceState({}, '', '/')
    } else if (params.get('auth_error')) {
      this.showMessage('Bank connection failed: ' + params.get('auth_error'), 'error')
      window.history.replaceState({}, '', '/')
    }
  },

  methods: {
    async fetchTransactions() {
      try {
        const res = await axios.get('http://localhost:8000/transactions')
        this.transactions = res.data
      } catch (e) {
        console.error(e)
      }
    },

    async connectBank() {
      this.connecting = true
      try {
        const res = await axios.get('http://localhost:8000/auth/link', {
          params: { country: 'SE', bank_name: 'SEB' },
        })
        window.location.href = res.data.url
      } catch (err) {
        this.showMessage('Could not connect: ' + (err.response?.data?.detail || err.message), 'error')
        this.connecting = false
      }
    },

    async syncTransactions() {
      this.syncing = true
      try {
        const res = await axios.post('http://localhost:8000/transactions/sync')
        const n = res.data.new_transactions
        this.showMessage(n > 0 ? `Synced ${n} new transaction${n === 1 ? '' : 's'}.` : 'Already up to date.')
        await this.fetchTransactions()
      } catch (err) {
        this.showMessage('Sync failed: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        this.syncing = false
      }
    },

    showMessage(text, type = 'success') {
      this.message = text
      this.messageType = type
      if (type === 'success') setTimeout(() => { this.message = '' }, 6000)
    },

    formatSEK(n) {
      return new Intl.NumberFormat('sv-SE', {
        minimumFractionDigits: 2, maximumFractionDigits: 2,
      }).format(Math.abs(n)) + ' kr'
    },

    toggleCategory(name) {
      const next = new Set(this.openCategories)
      next.has(name) ? next.delete(name) : next.add(name)
      this.openCategories = next
    },

    formatDate(d) {
      return new Date(d + 'T12:00:00').toLocaleDateString('sv-SE', { day: 'numeric', month: 'short' })
    },

    // Compact format for month cards (no decimals)
    compactSEK(n) {
      return new Intl.NumberFormat('sv-SE', {
        maximumFractionDigits: 0,
      }).format(Math.abs(n)) + ' kr'
    },
  },
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Hide scrollbar on the month selector row but keep it scrollable */
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
