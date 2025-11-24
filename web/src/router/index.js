import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../pages/Layout.vue'
import Notice from '../pages/Notice.vue'
import Mail from '../pages/Mail.vue'

const routes = [
  // 主应用页面
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'notice',
        name: 'Notice',
        component: Notice
      },
      {
        path: 'mail',
        name: 'Mail',
        component: Mail
      }
    ]
  },
  // 重定向旧的登录路径到首页
  {
    path: '/login',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router