import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/Home.vue') },
        { path: 'resume', name: 'resume', component: () => import('../views/Resume.vue') },
        { path: 'interview', name: 'interview', component: () => import('../views/Interview.vue') },
        { path: 'report', name: 'report', component: () => import('../views/Report.vue') },
      ],
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router

