<template>
  <div class="min-h-screen bg-gray-950">

    <!-- ── Navigation ──────────────────────────────────────────────────────── -->
    <nav class="bg-gray-900 border-b border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center h-16">

          <div class="flex items-center gap-8">
            <div class="flex items-center gap-2.5">
              <svg class="w-6 h-6 text-indigo-400 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="2"  y="14" width="4" height="8" rx="1.2" opacity="0.6"/>
                <rect x="9"  y="8"  width="4" height="14" rx="1.2" opacity="0.8"/>
                <rect x="16" y="3"  width="4" height="19" rx="1.2"/>
              </svg>
              <span class="text-white font-bold text-lg tracking-tight leading-none">Saldo</span>
              <span class="hidden sm:block text-gray-500 text-xs font-medium mt-0.5 pl-1 border-l border-gray-700">
                personal finance
              </span>
            </div>

            <div class="flex items-center gap-1">
              <router-link to="/" class="nav-link">Dashboard</router-link>
              <router-link to="/transactions" class="nav-link">Transactions</router-link>
            </div>
          </div>

        </div>
      </div>
    </nav>

    <!-- ── Page content ────────────────────────────────────────────────────── -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <router-view />
    </main>

  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
* {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.nav-link {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 500;
  color: #9ca3af;
  text-decoration: none;
  transition: color 0.15s, background 0.15s;
}

.nav-link:hover {
  color: #f9fafb;
  background: rgba(255, 255, 255, 0.07);
}

.router-link-active {
  color: #a5b4fc !important;
  background: rgba(99, 102, 241, 0.15) !important;
}
</style>
