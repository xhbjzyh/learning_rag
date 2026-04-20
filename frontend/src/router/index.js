import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

// 布局组件
import Layout from '@/components/Layout.vue'

const routes = [
  // 登录/注册 = 无布局
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue'),
    meta: { noAuth: true }
  },

  // 带侧边栏的主布局
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/pages/Chat.vue'),
        meta: { title: 'AI 问答' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/pages/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'personal',
        name: 'Personal',
        component: () => import('@/pages/Personal.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: '',
        redirect: '/chat'
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 🔥 修复：路由守卫逻辑
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 🔥 关键：初始化用户信息
  if (!userStore.token) {
    userStore.initUser()
  }

  const isLogin = !!userStore.token

  console.log('路由跳转:', to.path, '是否登录:', isLogin)

  // 无需登录的页面
  if (to.meta.noAuth) {
    next()
    return
  }

  // 未登录
  if (!isLogin) {
    console.log('未登录，跳转到登录页')
    next('/login')
    return
  }

  // 正常放行
  next()
})

export default router