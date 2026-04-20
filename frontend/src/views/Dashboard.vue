<template>
  <div>

    <!-- ── Header ──────────────────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-6">
      <div class="flex items-center gap-3">
        <h1 class="text-3xl font-bold text-gray-100">Dashboard</h1>
        <span v-if="isDemo" class="text-xs font-bold uppercase tracking-widest bg-amber-500/20 text-amber-400 border border-amber-500/40 px-2.5 py-1 rounded-full">
          Demo
        </span>
        <span v-else-if="isLive" class="flex items-center gap-1.5 text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/30 px-2.5 py-1 rounded-full">
          <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse inline-block"></span>
          Live
        </span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          @click="loadDemo"
          :disabled="loadingDemo"
          class="flex items-center gap-2 bg-gray-800 border border-gray-700 text-gray-400 px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          {{ loadingDemo ? 'Loading…' : 'Try Demo' }}
        </button>
        <button
          @click="connectBank"
          :disabled="connecting"
          class="flex items-center gap-2 bg-gray-800 border border-gray-700 text-gray-300 px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
          {{ connecting ? 'Connecting…' : 'Connect SEB' }}
        </button>
        <button
          @click="syncTransactions"
          :disabled="syncing"
          class="flex items-center gap-2 bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4 shrink-0" :class="{ 'animate-spin': syncing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ syncing ? 'Syncing…' : 'Sync' }}
        </button>
      </div>
    </div>

    <!-- ── Feedback banner ─────────────────────────────────────────────────── -->
    <transition name="fade">
      <div
        v-if="message"
        :class="messageType === 'success'
          ? 'bg-green-900/30 border-green-800 text-green-300'
          : 'bg-red-900/30 border-red-800 text-red-300'"
        class="mb-6 px-4 py-3 rounded-lg border text-sm font-medium flex justify-between items-center"
      >
        <span>{{ message }}</span>
        <button @click="message = ''" class="ml-4 opacity-60 hover:opacity-100 text-lg leading-none">&times;</button>
      </div>
    </transition>

    <!-- ── Loading skeleton ───────────────────────────────────────────────── -->
    <div v-if="loading" class="space-y-6 animate-pulse">
      <div class="flex gap-3">
        <div v-for="i in 5" :key="i" class="flex-shrink-0 w-36 h-20 bg-gray-800 rounded-xl" />
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="bg-gray-800 rounded-xl h-28" />
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-gray-800 rounded-xl h-80" />
        <div class="bg-gray-800 rounded-xl h-80" />
      </div>
    </div>

    <!-- ── Empty state ─────────────────────────────────────────────────────── -->
    <div v-else-if="transactions.length === 0" class="bg-gray-800 rounded-xl border border-gray-700 shadow-sm py-20 text-center">
      <div class="text-5xl mb-4">💳</div>
      <p class="text-gray-300 font-medium">No transactions yet</p>
      <p class="text-gray-500 text-sm mt-1">Connect your SEB account and click <strong class="text-gray-400">Sync Transactions</strong>.</p>
    </div>

    <template v-else>

      <!-- ── Mode banner ───────────────────────────────────────────────────── -->
      <div v-if="isDemo" class="mb-5 flex items-center gap-3 bg-amber-500/10 border border-amber-500/30 text-amber-300 px-4 py-3 rounded-lg text-sm font-medium">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span>You're viewing <strong>demo data</strong> with mock Swedish transactions — not your real bank data.</span>
      </div>
      <div v-else-if="isLive" class="mb-5 flex items-center gap-3 bg-green-500/10 border border-green-500/30 text-green-400 px-4 py-3 rounded-lg text-sm font-medium">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>You're viewing <strong>live bank data</strong> synced from your SEB account.</span>
      </div>

      <!-- ── Month selector ────────────────────────────────────────────────── -->
      <div class="flex gap-3 overflow-x-auto pb-3 mb-6 scrollbar-hide" ref="monthScroller">
        <button
          v-for="m in monthlySummaries"
          :key="m.key"
          :data-month="m.key"
          @click="selectedMonth = m.key"
          :class="selectedMonth === m.key
            ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
            : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-indigo-600 hover:shadow-sm'"
          class="flex-shrink-0 border rounded-xl px-5 py-3 text-left transition-all duration-150 cursor-pointer w-36"
        >
          <p class="text-sm font-bold leading-tight">{{ m.shortMonth }}</p>
          <p :class="selectedMonth === m.key ? 'text-indigo-200' : 'text-gray-500'" class="text-xs mb-2">
            {{ m.year }}
          </p>
          <p
            class="text-base font-bold"
            :class="selectedMonth === m.key
              ? (m.net >= 0 ? 'text-green-300' : 'text-red-300')
              : (m.net >= 0 ? 'text-green-500' : 'text-red-400')"
          >
            {{ m.net >= 0 ? '+' : '−' }}{{ compactSEK(m.net) }}
          </p>
        </button>
      </div>

      <!-- ── Month label ───────────────────────────────────────────────────── -->
      <h2 class="text-xl font-bold text-gray-200 mb-4">{{ selectedMonthLabel }}</h2>

      <!-- ── Summary cards ─────────────────────────────────────────────────── -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">

        <div class="bg-gray-800 p-5 rounded-xl shadow-sm border border-gray-700">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500 uppercase font-semibold tracking-wide">Income</p>
            <span class="text-xl">💰</span>
          </div>
          <p class="text-2xl font-bold text-green-400">+{{ formatSEK(selectedIncome) }}</p>
          <div v-if="incomeTrend !== null" class="mt-2 flex items-center gap-1 text-xs">
            <span :class="incomeTrend >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ incomeTrend >= 0 ? '▲' : '▼' }} {{ Math.abs(incomeTrend) }}%
            </span>
            <span class="text-gray-500">vs last month</span>
          </div>
        </div>

        <div class="bg-gray-800 p-5 rounded-xl shadow-sm border border-gray-700">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500 uppercase font-semibold tracking-wide">Expenses</p>
            <span class="text-xl">💸</span>
          </div>
          <p class="text-2xl font-bold text-red-400">−{{ formatSEK(selectedExpenses) }}</p>
          <div v-if="expensesTrend !== null" class="mt-2 flex items-center gap-1 text-xs">
            <span :class="expensesTrend <= 0 ? 'text-green-400' : 'text-red-400'">
              {{ expensesTrend >= 0 ? '▲' : '▼' }} {{ Math.abs(expensesTrend) }}%
            </span>
            <span class="text-gray-500">vs last month</span>
          </div>
        </div>

        <div class="bg-gray-800 p-5 rounded-xl shadow-sm border border-gray-700">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500 uppercase font-semibold tracking-wide">Net</p>
            <span class="text-xl">📊</span>
          </div>
          <p class="text-2xl font-bold" :class="selectedNet >= 0 ? 'text-indigo-400' : 'text-red-400'">
            {{ selectedNet >= 0 ? '+' : '−' }}{{ formatSEK(selectedNet) }}
          </p>
          <div v-if="netTrend !== null" class="mt-2 flex items-center gap-1 text-xs">
            <span :class="netTrend >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ netTrend >= 0 ? '▲' : '▼' }} {{ Math.abs(netTrend) }}%
            </span>
            <span class="text-gray-500">vs last month</span>
          </div>
        </div>

        <div class="bg-gray-800 p-5 rounded-xl shadow-sm border border-gray-700">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs text-gray-500 uppercase font-semibold tracking-wide">Saved</p>
            <span class="text-xl">🏦</span>
          </div>
          <p class="text-2xl font-bold" :class="savingsRate !== null && savingsRate >= 0 ? 'text-indigo-400' : 'text-red-400'">
            {{ savingsRate !== null ? savingsRate + '%' : '—' }}
          </p>
          <div v-if="savingsRate !== null" class="mt-2">
            <div class="w-full bg-gray-700 rounded-full h-1.5">
              <div
                class="h-1.5 rounded-full transition-all duration-500"
                :class="savingsRate >= 0 ? 'bg-indigo-500' : 'bg-red-500'"
                :style="{ width: Math.min(Math.abs(savingsRate), 100) + '%' }"
              />
            </div>
            <p class="text-xs text-gray-500 mt-1">of income</p>
          </div>
        </div>

      </div>

      <!-- ── Charts ────────────────────────────────────────────────────────── -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <div class="bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-700">
          <h3 class="text-base font-semibold text-gray-200 mb-4">Spending by Category</h3>
          <div class="h-64 flex justify-center">
            <Doughnut v-if="hasExpenses" :data="donutChartData" :options="donutOptions" />
            <p v-else class="text-gray-500 text-sm self-center">No expenses this month</p>
          </div>
        </div>

        <div class="bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-700">
          <h3 class="text-base font-semibold text-gray-200 mb-4">Monthly Overview</h3>
          <div class="h-64">
            <Bar :data="barChartData" :options="barOptions" />
          </div>
        </div>

      </div>

      <!-- ── Transactions for selected month ──────────────────────────────── -->
      <h3 class="text-base font-semibold text-gray-200 mt-8 mb-3">
        Transactions — {{ selectedMonthLabel }}
      </h3>

      <div class="space-y-2">
        <div
          v-for="cat in selectedCategories"
          :key="cat.name"
          class="bg-gray-800 rounded-xl shadow-sm border border-gray-700 overflow-hidden"
        >
          <button
            @click="toggleCategory(cat.name)"
            class="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-700/50 transition-colors text-left"
          >
            <div class="flex items-center gap-2 min-w-0">
              <svg
                class="w-4 h-4 text-gray-500 transition-transform shrink-0"
                :class="{ 'rotate-90': openCategories.has(cat.name) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
              <span class="text-lg leading-none shrink-0">{{ getCategoryIcon(cat.name) }}</span>
              <span class="text-sm font-semibold text-gray-200 truncate">{{ cat.name }}</span>
              <span class="hidden sm:inline text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded-full shrink-0">
                {{ cat.transactions.length }}
              </span>
            </div>
            <span class="text-sm font-bold shrink-0 ml-2" :class="cat.total >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ cat.total >= 0 ? '+' : '−' }}{{ formatSEK(cat.total) }}
            </span>
          </button>

          <div v-if="openCategories.has(cat.name)" class="border-t border-gray-700">
            <div
              v-for="t in cat.transactions"
              :key="t.id"
              class="flex items-center justify-between px-5 py-2.5 hover:bg-gray-700/50 border-b border-gray-700/50 last:border-0 transition-colors"
            >
              <div class="flex items-center gap-4 min-w-0">
                <span class="text-xs text-gray-500 w-14 shrink-0">{{ formatDate(t.date) }}</span>
                <span class="text-sm text-gray-400 truncate">{{ t.note || t.category }}</span>
              </div>
              <span class="text-sm font-medium shrink-0" :class="t.type === 'income' ? 'text-green-400' : 'text-red-400'">
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
import api from '../api'
import { Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  BarElement, CategoryScale, LinearScale,
} from 'chart.js'

const centerTextPlugin = {
  id: 'centerText',
  afterDraw(chart) {
    if (chart.config.type !== 'doughnut') return
    const { ctx, chartArea } = chart
    if (!chartArea) return
    const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0)
    const formatted = new Intl.NumberFormat('sv-SE', { maximumFractionDigits: 0 }).format(total) + ' kr'
    const cx = (chartArea.left + chartArea.right) / 2
    const cy = (chartArea.top + chartArea.bottom) / 2
    ctx.save()
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = 'bold 13px system-ui, sans-serif'
    ctx.fillStyle = '#f3f4f6'
    ctx.fillText(formatted, cx, cy - 9)
    ctx.font = '11px system-ui, sans-serif'
    ctx.fillStyle = '#6b7280'
    ctx.fillText('total spent', cx, cy + 9)
    ctx.restore()
  },
}

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale, centerTextPlugin)

const COLORS = ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#f97316']

const CATEGORY_ICONS = [
  [/ica|coop|lidl|willys|hemköp|hemkop|mat|grocery|livs|netto|maxi/i, '🛒'],
  [/restaurang|restaurant|café|cafe|pizza|sushi|mcdonald|burger|kfc|kebab|bar |pub|bistro/i, '🍽️'],
  [/sl |buss|tåg|tag|taxi|uber|bolt|transport|parkering|parking|train|flyg|flight|trafik/i, '🚌'],
  [/lön|lon|salary|income|arbets|employer/i, '💰'],
  [/uttag|atm|bankomat|kontant|cash/i, '🏧'],
  [/kläder|klader|clothes|h&m|zara|asos|fashion|nk |åhlens|ahlens/i, '🛍️'],
  [/bensin|fuel|gas|shell|circle k|st1|preem|okq8/i, '⛽'],
  [/apotek|pharmacy|läkare|lakare|doctor|health|dental|tandläk|tandlak|vård|vard/i, '💊'],
  [/netflix|spotify|youtube|hbo|disney|viaplay|streaming|apple|adobe/i, '📺'],
  [/försäkring|forsakring|insurance/i, '🛡️'],
  [/hyra|rent|brf|housing|bostad/i, '🏠'],
  [/el |electricity|vattenfall|fortum|tibber|eon |energi/i, '⚡'],
  [/gym|träning|traning|fitness|sport|friskis/i, '🏋️'],
  [/swish|transfer|överföring|overforing/i, '🔄'],
  [/ränta|ranta|interest|amortering|loan|lån|lan |bank|skandia|nordea|handels/i, '🏦'],
  [/internet|bredband|tele|mobil|telia|telenor|comviq/i, '📡'],
]

export default {
  components: { Doughnut, Bar },

  data() {
    return {
      transactions: [],
      loading: true,
      selectedMonth: null,
      syncing: false,
      connecting: false,
      loadingDemo: false,
      isDemo: false,
      isLive: false,
      message: '',
      messageType: 'success',
      openCategories: new Set(),
      donutOptions: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#9ca3af', boxWidth: 12, font: { size: 11 } },
          },
        },
      },
      barOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#9ca3af', boxWidth: 12, font: { size: 11 } } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#6b7280' } },
          y: { grid: { color: '#374151' }, ticks: { color: '#6b7280' } },
        },
      },
    }
  },

  computed: {
    monthlySummaries() {
      const map = {}
      for (const t of this.transactions) {
        const key = t.date.substring(0, 7)
        if (!map[key]) map[key] = { income: 0, expenses: 0 }
        if (t.type === 'income') map[key].income += t.amount
        else map[key].expenses += t.amount
      }
      return Object.keys(map)
        .sort((a, b) => b.localeCompare(a))
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
    savingsRate() {
      if (this.selectedIncome === 0) return null
      return Math.round((this.selectedNet / this.selectedIncome) * 100)
    },

    prevMonthKey() {
      if (!this.selectedMonth) return null
      const [y, m] = this.selectedMonth.split('-').map(Number)
      const d = new Date(y, m - 2)
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    },
    prevMonthTxs() {
      if (!this.prevMonthKey) return []
      return this.transactions.filter(t => t.date.startsWith(this.prevMonthKey))
    },
    prevMonthIncome() {
      return this.prevMonthTxs.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0)
    },
    prevMonthExpenses() {
      return this.prevMonthTxs.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0)
    },
    prevMonthNet() {
      return this.prevMonthIncome - this.prevMonthExpenses
    },
    incomeTrend()   { return this.calcTrend(this.selectedIncome, this.prevMonthIncome) },
    expensesTrend() { return this.calcTrend(this.selectedExpenses, this.prevMonthExpenses) },
    netTrend() {
      if (this.prevMonthNet === 0) return null
      return Math.round(((this.selectedNet - this.prevMonthNet) / Math.abs(this.prevMonthNet)) * 100)
    },

    hasExpenses() {
      return this.selectedTxs.some(t => t.type === 'expense')
    },

    donutChartData() {
      const catMap = {}
      for (const t of this.selectedTxs.filter(t => t.type === 'expense')) {
        catMap[t.category] = (catMap[t.category] || 0) + t.amount
      }
      const sorted = Object.entries(catMap).sort(([, a], [, b]) => b - a).slice(0, 8)
      return {
        labels: sorted.map(([k]) => k),
        datasets: [{
          data: sorted.map(([, v]) => v),
          backgroundColor: COLORS,
          borderWidth: 0,
          hoverOffset: 6,
        }],
      }
    },

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
        .sort((a, b) => a.total - b.total)
    },

    barChartData() {
      const all = [...this.monthlySummaries].reverse()
      return {
        labels: all.map(m => `${m.shortMonth} ${m.year.slice(2)}`),
        datasets: [
          {
            label: 'Income',
            data: all.map(m => m.income),
            backgroundColor: all.map(m => m.key === this.selectedMonth ? '#059669' : '#064e3b'),
            borderRadius: 4,
          },
          {
            label: 'Expenses',
            data: all.map(m => m.expenses),
            backgroundColor: all.map(m => m.key === this.selectedMonth ? '#dc2626' : '#450a0a'),
            borderRadius: 4,
          },
        ],
      }
    },
  },

  watch: {
    monthlySummaries(summaries) {
      if (!this.selectedMonth && summaries.length > 0) {
        this.selectedMonth = summaries[0].key
      }
    },
    selectedMonth(key) {
      this.openCategories = new Set()
      this.$nextTick(() => {
        const el = this.$refs.monthScroller?.querySelector(`[data-month="${key}"]`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      })
    },
  },

  async mounted() {
    const params = new URLSearchParams(window.location.search)
    if (params.get('sync') === 'success') {
      this.showMessage('SEB connected! Click "Sync Transactions" to import your data.')
      window.history.replaceState({}, '', '/')
      await this.fetchTransactions()
    } else if (params.get('auth_error')) {
      this.showMessage('Bank connection failed: ' + params.get('auth_error'), 'error')
      window.history.replaceState({}, '', '/')
      await this.fetchTransactions()
    } else {
      // Always show demo by default — visitors should never see real bank data
      await this.loadDemo()
    }
  },

  methods: {
    async fetchTransactions() {
      this.loading = true
      try {
        const res = await api.get('/transactions')
        this.transactions = res.data
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },

    async loadDemo() {
      this.loadingDemo = true
      try {
        await api.post('/demo/seed')
        this.isDemo = true
        this.selectedMonth = null
        await this.fetchTransactions()
      } catch (err) {
        this.showMessage('Could not load demo: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        this.loadingDemo = false
      }
    },

    async connectBank() {
      this.connecting = true
      this.showMessage('Waking up backend… this may take up to 30 seconds on first load.', 'success')
      try {
        // Render free tier spins down after inactivity — poll /health until the
        // service is fully awake before starting the bank auth flow. This ensures
        // the /auth/callback redirect (which arrives ~60s later) hits a live server.
        const deadline = Date.now() + 60_000
        while (Date.now() < deadline) {
          try {
            await api.get('/health', { timeout: 5000 })
            break // backend is awake
          } catch {
            await new Promise(r => setTimeout(r, 3000))
          }
        }
        this.message = ''
        const res = await api.get('/auth/link', {
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
        const res = await api.post('/transactions/sync')
        const n = res.data.new_transactions
        this.isDemo = false
        this.isLive = true
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

    compactSEK(n) {
      return new Intl.NumberFormat('sv-SE', { maximumFractionDigits: 0 }).format(Math.abs(n)) + ' kr'
    },

    calcTrend(current, prev) {
      if (prev === 0) return null
      return Math.round(((current - prev) / prev) * 100)
    },

    getCategoryIcon(name) {
      for (const [pattern, icon] of CATEGORY_ICONS) {
        if (pattern.test(name)) return icon
      }
      return '📋'
    },
  },
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
