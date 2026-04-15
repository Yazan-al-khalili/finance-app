<template>
  <div class="min-h-screen bg-gray-100">
    <nav class="bg-indigo-600 text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <span class="text-xl font-bold tracking-wider">FinanceApp</span>
            <div class="ml-10 flex items-baseline space-x-4">
              <router-link to="/" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors">Dashboard</router-link>
              <router-link to="/transactions" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors">Transactions</router-link>
            </div>
          </div>
        </div>
      </div>
    </nav>
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
.router-link-active {
  background-color: #4f46e5;
}
</style>
