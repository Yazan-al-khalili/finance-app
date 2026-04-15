<template>
  <div>
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Transactions</h1>
    <TransactionForm @transaction-added="fetchTransactions" />
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Note</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="t in transactions" :key="t.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ t.date }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm capitalize">
              <span :class="t.type === 'income' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'">
                {{ t.type }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ t.category }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium" :class="t.type === 'income' ? 'text-green-600' : 'text-red-600'">
              {{ t.type === 'income' ? '+' : '-' }}${{ t.amount.toFixed(2) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ t.note }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <button @click="deleteTransaction(t.id)" class="text-red-600 hover:text-red-900 transition-colors">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import TransactionForm from '../components/TransactionForm.vue'

export default {
  components: { TransactionForm },
  data() {
    return {
      transactions: []
    }
  },
  mounted() {
    this.fetchTransactions()
  },
  methods: {
    async fetchTransactions() {
      try {
        const response = await axios.get('http://localhost:8000/transactions')
        this.transactions = response.data
      } catch (error) {
        console.error('Error fetching transactions:', error)
      }
    },
    async deleteTransaction(id) {
      if (!confirm('Are you sure?')) return
      try {
        await axios.delete(`http://localhost:8000/transactions/${id}`)
        this.fetchTransactions()
      } catch (error) {
        console.error('Error deleting transaction:', error)
      }
    }
  }
}
</script>
