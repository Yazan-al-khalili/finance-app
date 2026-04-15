<template>
  <div>
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Dashboard</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-lg shadow-md border-t-4 border-indigo-500">
        <p class="text-sm text-gray-500 uppercase font-semibold">Total Balance</p>
        <p class="text-3xl font-bold" :class="balance >= 0 ? 'text-green-600' : 'text-red-600'">
          ${{ balance.toFixed(2) }}
        </p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md border-t-4 border-green-500">
        <p class="text-sm text-gray-500 uppercase font-semibold">Income</p>
        <p class="text-3xl font-bold text-green-600">${{ totalIncome.toFixed(2) }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md border-t-4 border-red-500">
        <p class="text-sm text-gray-500 uppercase font-semibold">Expenses</p>
        <p class="text-3xl font-bold text-red-600">${{ totalExpenses.toFixed(2) }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-bold mb-4 text-gray-800">Spending by Category</h2>
        <div class="h-64 flex justify-center">
          <Pie v-if="hasData" :data="pieChartData" :options="chartOptions" />
          <p v-else class="text-gray-500 italic mt-20">No data to display</p>
        </div>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-bold mb-4 text-gray-800">Income vs Expenses</h2>
        <div class="h-64 flex justify-center">
          <Bar v-if="hasData" :data="barChartData" :options="chartOptions" />
          <p v-else class="text-gray-500 italic mt-20">No data to display</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { Pie, Bar } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default {
  components: { Pie, Bar },
  data() {
    return {
      transactions: [],
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false
      }
    }
  },
  computed: {
    hasData() {
      return this.transactions.length > 0
    },
    balance() {
      return this.transactions.reduce((acc, t) => {
        return t.type === 'income' ? acc + t.amount : acc - t.amount
      }, 0)
    },
    totalIncome() {
      return this.transactions
        .filter(t => t.type === 'income')
        .reduce((acc, t) => acc + t.amount, 0)
    },
    totalExpenses() {
      return this.transactions
        .filter(t => t.type === 'expense')
        .reduce((acc, t) => acc + t.amount, 0)
    },
    pieChartData() {
      const expenses = this.transactions.filter(t => t.type === 'expense')
      const categories = [...new Set(expenses.map(t => t.category))]
      const data = categories.map(cat => {
        return expenses
          .filter(t => t.category === cat)
          .reduce((acc, t) => acc + t.amount, 0)
      })

      return {
        labels: categories,
        datasets: [{
          data: data,
          backgroundColor: [
            '#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'
          ]
        }]
      }
    },
    barChartData() {
      // Group by month
      const months = {}
      this.transactions.forEach(t => {
        const month = t.date.substring(0, 7) // YYYY-MM
        if (!months[month]) months[month] = { income: 0, expense: 0 }
        months[month][t.type] += t.amount
      })

      const sortedMonths = Object.keys(months).sort()
      
      return {
        labels: sortedMonths,
        datasets: [
          {
            label: 'Income',
            backgroundColor: '#10b981',
            data: sortedMonths.map(m => months[m].income)
          },
          {
            label: 'Expenses',
            backgroundColor: '#ef4444',
            data: sortedMonths.map(m => months[m].expense)
          }
        ]
      }
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
    }
  }
}
</script>
