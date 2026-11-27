<template>
  <div class="relative h-screen overflow-hidden md:flex">
    <!-- Mobile Menu Header -->
    <div class="bg-paper-sidebar text-gray-100 flex justify-between md:hidden shrink-0">
      <router-link to="/" class="block p-4 text-white font-bold">{{ SYSTEM_TITLE }}</router-link>
      <button
        type="button"
        @click="sidebarOpen = !sidebarOpen"
        class="p-4 focus:outline-none focus:bg-paper-active-link"
        aria-label="Abrir menu lateral"
      >
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Sidebar (Expansível / Recolhível) -->
    <aside
      :class="[
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        isCollapsed ? 'md:w-20' : 'md:w-64'
      ]"
      class="bg-paper-sidebar text-gray-100 pt-7 pb-2 px-2 absolute inset-y-0 left-0 transform md:relative md:translate-x-0 transition-all duration-300 ease-in-out z-20 h-full shrink-0 flex flex-col justify-between overflow-y-auto"
    >
      <div>
        <!-- Clique em "Nome do Sistema" recolhe/expande a barra lateral -->
        <div
          @click="toggleSidebar"
          title="Clique para recolher / expandir o menu"
          class="cursor-pointer text-white flex items-center space-x-3 px-3 mb-6 hover:opacity-90 transition duration-150 group"
        >
          <CubeTransparentIcon class="h-8 w-8 shrink-0 group-hover:scale-105 transition-transform" />
          <span v-if="!isCollapsed" class="text-xl font-extrabold leading-snug break-words select-none">
            {{ SYSTEM_TITLE }}
          </span>
        </div>

        <div class="px-3 my-4">
          <div class="border-t border-white border-opacity-20"></div>
        </div>

        <!-- Links de Navegação -->
        <nav class="space-y-1.5">
          <router-link
            to="/"
            :title="isCollapsed ? 'Início' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <HomeIcon class="h-6 w-6 shrink-0" />
            <span v-if="!isCollapsed" class="truncate">Início</span>
          </router-link>

          <template v-if="authStore.isAuthenticated">
            <router-link
              to="/fila"
              :title="isCollapsed ? `Fila de Exames${vencidos24h > 0 ? ` (${vencidos24h} vencidos)` : ''}` : ''"
              :class="[isCollapsed ? 'justify-center px-2 relative' : 'px-4 justify-between']"
              class="flex items-center py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <span class="flex items-center space-x-3 min-w-0">
                <QueueListIcon class="h-6 w-6 shrink-0" />
                <span v-if="!isCollapsed" class="truncate">Fila de Exames</span>
              </span>
              <span
                v-if="vencidos24h > 0 && !isCollapsed"
                class="ml-2 inline-flex items-center justify-center rounded-full bg-red-600/90 px-2 py-0.5 text-[11px] font-bold text-white tabular-nums shrink-0"
                title="Prazos de confirmação 24h vencidos"
              >
                {{ vencidos24h }}
              </span>
              <span
                v-else-if="vencidos24h > 0 && isCollapsed"
                class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500"
                aria-hidden="true"
              ></span>
            </router-link>

            <router-link
              to="/importacao"
              :title="isCollapsed ? 'Importação Forms' : ''"
              :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
              class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <ArrowUpTrayIcon class="h-6 w-6 shrink-0" />
              <span v-if="!isCollapsed" class="truncate">Importação Forms</span>
            </router-link>

            <router-link
              to="/regras"
              :title="isCollapsed ? 'Regras de Triagem' : ''"
              :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
              class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <AdjustmentsHorizontalIcon class="h-6 w-6 shrink-0" />
              <span v-if="!isCollapsed" class="truncate">Regras de Triagem</span>
            </router-link>

            <router-link
              to="/dashboard"
              :title="isCollapsed ? 'Dashboard KPIs' : ''"
              :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
              class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <ChartBarIcon class="h-6 w-6 shrink-0" />
              <span v-if="!isCollapsed" class="truncate">Dashboard KPIs</span>
            </router-link>

            <div class="px-2 py-1.5">
              <div class="border-t border-white/10"></div>
            </div>

            <router-link
              to="/configuracoes"
              :title="isCollapsed ? 'Configurações' : ''"
              :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
              class="flex items-center space-x-3 py-2.5 rounded transition duration-200 hover:bg-paper-active-link hover:text-white"
            >
              <Cog6ToothIcon class="h-6 w-6 shrink-0" />
              <span v-if="!isCollapsed" class="truncate">Configurações</span>
            </router-link>
          </template>

          <div class="px-2 py-1.5">
            <div class="border-t border-white/10"></div>
          </div>

          <router-link
            to="/componentes"
            :title="isCollapsed ? 'Componentes' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2 rounded text-sm text-gray-300 transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <CubeIcon class="h-5 w-5 shrink-0" />
            <span v-if="!isCollapsed" class="truncate">Componentes</span>
          </router-link>

          <router-link
            v-if="authStore.isAuthenticated"
            to="/exemplo"
            :title="isCollapsed ? 'Pacientes (Ref)' : ''"
            :class="[isCollapsed ? 'justify-center px-2' : 'px-4']"
            class="flex items-center space-x-3 py-2 rounded text-sm text-gray-300 transition duration-200 hover:bg-paper-active-link hover:text-white"
          >
            <DocumentTextIcon class="h-5 w-5 shrink-0" />
            <span v-if="!isCollapsed" class="truncate">Pacientes (Ref)</span>
          </router-link>
        </nav>
      </div>

      <!-- Rodapé de Versão da Sidebar -->
      <div
        v-if="!isCollapsed"
        class="px-4 pt-3 pb-1 border-t border-white/10 text-xs text-gray-400 mt-auto truncate transition-opacity duration-200"
      >
        <p class="font-semibold text-gray-200 truncate">{{ APP_NAME }}</p>
        <p class="text-[11px] text-gray-400 truncate">Versão {{ APP_VERSION }} | HC-UFPE</p>
      </div>
      <div
        v-else
        class="px-2 pt-3 pb-1 border-t border-white/10 text-[10px] text-center text-gray-400 mt-auto"
      >
        v{{ APP_VERSION }}
      </div>
    </aside>

    <!-- Content -->
    <div class="flex-1 flex flex-col bg-paper-bg overflow-y-auto h-full">
      <header class="flex justify-between items-center p-6 bg-white/80 backdrop-blur-md border-b border-gray-300 sticky top-0 z-10">
        <div>
          <h1 class="text-2xl font-semibold text-paper-text">{{ $route.name }}</h1>
        </div>
        <div>
          <router-link v-if="!authStore.isAuthenticated" to="/login">
            <Button variant="primary">
              <template #icon>
                <ArrowRightOnRectangleIcon class="h-5 w-5" />
              </template>
              Login
            </Button>
          </router-link>
          <ProfileDropdown v-else />
        </div>
      </header>
      <main class="flex-1">
        <div class="container py-4 md:py-6">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  HomeIcon,
  CubeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  CubeTransparentIcon,
  Bars3Icon,
  ArrowRightOnRectangleIcon,
  QueueListIcon,
  ArrowUpTrayIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import Button from '../components/Button.vue';
import { useAuthStore } from '../stores/auth';
import { useExamesStore } from '../stores/exames';
import { APP_VERSION, APP_NAME, SYSTEM_TITLE } from '../config/version';

const sidebarOpen = ref(false);
const isCollapsed = ref(false);

const route = useRoute();
const authStore = useAuthStore();
const examesStore = useExamesStore();

const vencidos24h = computed(() => examesStore.resumoOperacional.vencidos24h);

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

// Close mobile sidebar on route change
watch(
  () => route.path,
  () => {
    sidebarOpen.value = false;
  },
);
</script>
