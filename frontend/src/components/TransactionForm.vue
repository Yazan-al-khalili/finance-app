<template>
  <div class="bg-gray-800 border border-gray-700 p-6 rounded-xl shadow-sm mb-6">
    <h2 class="text-base font-semibold text-gray-200 mb-4">Add Transaction</h2>
    <form @submit.prevent="handleSubmit" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div>
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Type</label>
        <select v-model="form.type" class="mt-1 block w-full rounded-lg border border-gray-600 bg-gray-700 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 text-sm">
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Category</label>
        <input v-model="form.category" type="text" placeholder="e.g. Food, Salary" class="mt-1 block w-full rounded-lg border border-gray-600 bg-gray-700 text-gray-200 placeholder-gray-500 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 text-sm" required>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Amount</label>
        <input v-model.number="form.amount" type="number" step="0.01" class="mt-1 block w-full rounded-lg border border-gray-600 bg-gray-700 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 text-sm" required>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Date</label>
        <input v-model="form.date" type="date" class="mt-1 block w-full rounded-lg border border-gray-600 bg-gray-700 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 text-sm" required>
      </div>
      <div class="md:col-span-2">
        <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Note</label>
        <input v-model="form.note" type="text" placeholder="Optional note" class="mt-1 block w-full rounded-lg border border-gray-600 bg-gray-700 text-gray-200 placeholder-gray-500 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 text-sm">
      </div>
      <div class="lg:col-span-3 flex justify-end">
        <button type="submit" class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm text-sm font-semibold">
          Add Transaction
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import api from '../api'

export default {
  data() {
    return {
      form: {
        type: 'expense',
        category: '',
        amount: 0,
        date: new Date().toISOString().substr(0, 10),
        note: ''
      }
    }
  },
  methods: {
    async handleSubmit() {
      try {
        await api.post('/transactions', this.form)
        this.$emit('transaction-added')
        this.resetForm()
      } catch (error) {
        console.error('Error adding transaction:', error)
        alert('Failed to add transaction')
      }
    },
    resetForm() {
      this.form = {
        type: 'expense',
        category: '',
        amount: 0,
        date: new Date().toISOString().substr(0, 10),
        note: ''
      }
    }
  }
}
</script>
