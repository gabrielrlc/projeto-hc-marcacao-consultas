import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Configuracoes from '../views/Configuracoes.vue';
import Exemplos from '../views/Exemplos.vue';
import Pacientes from '../views/Pacientes.vue';
import FilaExames from '../views/FilaExames.vue';
import ImportacaoForms from '../views/ImportacaoForms.vue';
import RegrasConfiguracao from '../views/RegrasConfiguracao.vue';
import DashboardKpis from '../views/DashboardKpis.vue';

const routes = [
  {
    path: '/',
    name: 'Início',
    component: Home,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/fila',
    name: 'Fila de Exames',
    component: FilaExames,
    meta: { requiresAuth: true },
  },
  {
    path: '/importacao',
    name: 'Importação Forms',
    component: ImportacaoForms,
    meta: { requiresAuth: true },
  },
  {
    path: '/regras',
    name: 'Regras de Triagem',
    component: RegrasConfiguracao,
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard de KPIs',
    component: DashboardKpis,
    meta: { requiresAuth: true },
  },
  {
    path: '/componentes',
    name: 'Componentes',
    component: Exemplos,
  },
  {
    path: '/exemplo',
    name: 'Exemplo',
    component: Pacientes,
    meta: { requiresAuth: true },
  },
  {
    path: '/configuracoes',
    name: 'Configuracoes',
    component: Configuracoes,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-paper-active-link',
  linkExactActiveClass: 'bg-paper-active-link',
});

router.beforeEach((to, _from, next: NavigationGuardNext) => {
  // Pinia store must be used inside a function to ensure it's initialized
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;
