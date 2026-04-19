<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-6">
      <h1 class="text-3xl font-bold text-gray-100">Transactions</h1>
      <div class="flex flex-wrap gap-2 items-center">
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
          @click="syncBank"
          :disabled="syncing"
          class="flex items-center gap-2 bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm text-sm font-medium disabled:opacity-50"
        >
          <svg class="w-4 h-4 shrink-0" :class="{ 'animate-spin': syncing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ syncing ? 'Syncing…' : 'Sync' }}
        </button>

        <button
          v-if="transactions.length > 0"
          @click="clearAll"
          class="text-xs text-gray-400 hover:text-red-500 transition-colors px-2 py-1"
          title="Clear all transactions"
        >
          Clear data
        </button>
      </div>
    </div>

    <!-- Feedback banner -->
    <transition name="fade">
      <div
        v-if="message"
        :class="messageType === 'success'
          ? 'bg-green-900/30 border-green-800 text-green-300'
          : 'bg-red-900/30 border-red-800 text-red-300'"
        class="mb-5 px-4 py-3 rounded-lg border text-sm font-medium flex justify-between items-center"
      >
        <span>{{ message }}</span>
        <button @click="message = ''" class="ml-4 opacity-60 hover:opacity-100 text-lg leading-none">&times;</button>
      </div>
    </transition>

    <!-- Add transaction form -->
    <TransactionForm @transaction-added="fetchTransactions" />

    <!-- Empty state -->
    <div v-if="transactions.length === 0" class="bg-gray-800 rounded-xl shadow-sm border border-gray-700 py-16 text-center">
      <p class="text-gray-500 text-sm">No transactions yet.</p>
      <p class="text-gray-500 text-sm mt-1">Connect your SEB account and click <strong>Sync from SEB</strong>.</p>
    </div>

    <!-- Month sections -->
    <div v-for="month in grouped" :key="month.key" class="mb-8">

      <!-- Month header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-3 px-1">
        <h2 class="text-lg font-bold text-gray-100">{{ month.label }}</h2>
        <div class="flex items-center gap-3 sm:gap-5 text-sm">
          <span class="text-green-500 font-medium">+{{ formatSEK(month.totalIncome) }}</span>
          <span class="text-red-400 font-medium">−{{ formatSEK(month.totalExpenses) }}</span>
          <span class="font-bold" :class="month.net >= 0 ? 'text-indigo-400' : 'text-red-400'">
            {{ month.net >= 0 ? '+' : '−' }}{{ formatSEK(month.net) }}
          </span>
        </div>
      </div>

      <!-- Category cards -->
      <div class="space-y-2">
        <div
          v-for="cat in month.categories"
          :key="cat.name"
          class="bg-gray-800 rounded-xl shadow-sm border border-gray-700 overflow-hidden"
        >
          <!-- Category row (click to expand/collapse) -->
          <button
            @click="toggleCategory(month.key, cat.name)"
            class="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-700/50 transition-colors text-left"
          >
            <div class="flex items-center gap-2 min-w-0">
              <!-- Chevron -->
              <svg
                class="w-4 h-4 text-gray-500 transition-transform shrink-0"
                :class="{ 'rotate-90': isOpen(month.key, cat.name) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>

              <!-- Category icon + name -->
              <span class="text-lg leading-none shrink-0">{{ getCategoryIcon(cat.name) }}</span>
              <span class="text-sm font-semibold text-gray-100 truncate">{{ cat.name }}</span>

              <!-- Transaction count badge -->
              <span class="hidden sm:inline text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded-full shrink-0">
                {{ cat.transactions.length }}
              </span>
            </div>

            <!-- Category total -->
            <span
              class="text-sm font-bold shrink-0 ml-2"
              :class="cat.total >= 0 ? 'text-green-400' : 'text-red-400'"
            >
              {{ cat.total >= 0 ? '+' : '−' }}{{ formatSEK(cat.total) }}
            </span>
          </button>

          <!-- Expanded transaction rows -->
          <div v-if="isOpen(month.key, cat.name)" class="border-t border-gray-700">
            <div
              v-for="t in cat.transactions"
              :key="t.id"
              class="flex items-center justify-between px-5 py-2.5 hover:bg-gray-700/50 transition-colors border-b border-gray-700/50 last:border-0"
            >
              <!-- Date + note -->
              <div class="flex items-center gap-4 min-w-0">
                <span class="text-xs text-gray-500 w-14 shrink-0">{{ formatDate(t.date) }}</span>
                <span class="text-sm text-gray-400 truncate">{{ t.note || t.category }}</span>
              </div>

              <!-- Amount + delete -->
              <div class="flex items-center gap-4 shrink-0">
                <span
                  class="text-sm font-medium"
                  :class="t.type === 'income' ? 'text-green-600' : 'text-red-500'"
                >
                  {{ t.type === 'income' ? '+' : '−' }}{{ formatSEK(t.amount) }}
                </span>
                <button
                  @click.stop="deleteTransaction(t.id)"
                  class="text-gray-200 hover:text-red-400 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import TransactionForm from '../components/TransactionForm.vue'

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
  components: { TransactionForm },

  data() {
    return {
      transactions: [],
      syncing: false,
      connecting: false,
      message: '',
      messageType: 'success',
      // Tracks which category rows are expanded: Set of "monthKey|categoryName"
      expanded: new Set(),
    }
  },

  computed: {
    grouped() {
      // ── 1. Bucket by month ────────────────────────────────────────────────
      const monthMap = {}
      for (const t of this.transactions) {
        const key = t.date.substring(0, 7)   // "2024-03"
        if (!monthMap[key]) monthMap[key] = []
        monthMap[key].push(t)
      }

      return Object.keys(monthMap)
        .sort((a, b) => b.localeCompare(a))  // newest month first
        .map(key => {
          const txs = monthMap[key]
          const [year, mon] = key.split('-')
          const label = new Date(year, mon - 1).toLocaleString('en-US', {
            month: 'long', year: 'numeric',
          })

          // ── 2. Bucket by category within this month ─────────────────────
          const catMap = {}
          for (const t of txs) {
            const name = t.category || 'Other'
            if (!catMap[name]) catMap[name] = []
            catMap[name].push(t)
          }

          const categories = Object.keys(catMap)
            .map(name => {
              const catTxs = [...catMap[name]].sort((a, b) => b.date.localeCompare(a.date))
              const total = catTxs.reduce(
                (s, t) => t.type === 'income' ? s + t.amount : s - t.amount, 0
              )
              return { name, transactions: catTxs, total }
            })
            // Sort: biggest expense categories first, income at the bottom
            .sort((a, b) => a.total - b.total)

          const totalIncome   = txs.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0)
          const totalExpenses = txs.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0)
          const net = totalIncome - totalExpenses

          return { key, label, categories, totalIncome, totalExpenses, net }
        })
    },
  },

  mounted() {
    this.fetchTransactions()
  },

  methods: {
    async fetchTransactions() {
      const res = await api.get('/transactions')
      this.transactions = res.data
    },

    // ── Category expand / collapse ──────────────────────────────────────────
    toggleCategory(monthKey, catName) {
      const id = `${monthKey}|${catName}`
      const next = new Set(this.expanded)
      next.has(id) ? next.delete(id) : next.add(id)
      this.expanded = next
    },
    isOpen(monthKey, catName) {
      return this.expanded.has(`${monthKey}|${catName}`)
    },

    // ── Bank actions ────────────────────────────────────────────────────────
    async connectBank() {
      this.connecting = true
      try {
        const res = await api.get('/auth/link', {
          params: { country: 'SE', bank_name: 'SEB' },
        })
        window.location.href = res.data.url
      } catch (err) {
        this.showMessage('Could not start bank connection: ' + (err.response?.data?.detail || err.message), 'error')
        this.connecting = false
      }
    },

    async syncBank() {
      this.syncing = true
      this.message = ''
      try {
        const res = await api.post('/transactions/sync')
        const n = res.data.new_transactions
        this.showMessage(
          n > 0
            ? `Synced ${n} new transaction${n === 1 ? '' : 's'} from SEB.`
            : 'Already up to date — no new transactions found.'
        )
        await this.fetchTransactions()
      } catch (err) {
        this.showMessage('Sync failed: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        this.syncing = false
      }
    },

    async clearAll() {
      const n = this.transactions.length
      if (!confirm(`Delete all ${n} transactions? This cannot be undone.`)) return
      await api.delete('/transactions/all')
      this.transactions = []
      this.expanded = new Set()
      this.showMessage(`Cleared ${n} transactions.`)
    },

    async deleteTransaction(id) {
      if (!confirm('Delete this transaction?')) return
      await api.delete(`/transactions/${id}`)
      await this.fetchTransactions()
    },

    // ── Formatting ──────────────────────────────────────────────────────────
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

    formatDate(d) {
      return new Date(d + 'T12:00:00').toLocaleDateString('sv-SE', {
        day: 'numeric', month: 'short',
      })
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
</style>
