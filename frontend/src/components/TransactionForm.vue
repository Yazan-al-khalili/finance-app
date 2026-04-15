<template>
  <div class="bg-white p-6 rounded-lg shadow-md mb-6">
    <h2 class="text-xl font-bold mb-4 text-gray-800">Add Transaction</h2>
    <form @submit.prevent="handleSubmit" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Type</label>
        <select v-model="form.type" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2">
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Category</label>
        <input v-model="form.category" type="text" placeholder="e.g. Food, Salary" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2" required>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Amount</label>
        <input v-model.number="form.amount" type="number" step="0.01" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2" required>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Date</label>
        <input v-model="form.date" type="date" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2" required>
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Note</label>
        <input v-model="form.note" type="text" placeholder="Optional note" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2">
      </div>
      <div class="lg:col-span-3 flex justify-end">
        <button type="submit" class="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 transition-colors shadow-sm font-semibold">
          Add Transaction
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios'

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
        await axios.post('http://localhost:8000/transactions', this.form)
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
