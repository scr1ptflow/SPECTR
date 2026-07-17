import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        { path: '', name: 'bridge', component: () => import('@/pages/BridgePage.vue') },
        { path: 'navigation', name: 'navigation', component: () => import('@/pages/NavigationPage.vue') },
        { path: 'ship', name: 'ship', component: () => import('@/pages/ShipPage.vue') },
        { path: 'engineering', name: 'engineering', component: () => import('@/pages/EngineeringPage.vue') },
        { path: 'missions', name: 'missions', component: () => import('@/pages/MissionsPage.vue') },
        { path: 'exploration', name: 'exploration', component: () => import('@/pages/ExplorationPage.vue') },
        { path: 'commander', name: 'commander', component: () => import('@/pages/CommanderPage.vue') },
        { path: 'intelligence', name: 'intelligence', component: () => import('@/pages/IntelligencePage.vue') },
        { path: 'archive', name: 'archive', component: () => import('@/pages/ArchivePage.vue') },
      ],
    },
  ],
})

export default router
