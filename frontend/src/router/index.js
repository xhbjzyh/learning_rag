import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

// 公共路由
const publicRoutes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' }
  }
]

// 角色路由
import adminRoutes from './admin'
import auditorRoutes from './auditor'
import userRoutes from './user'

// 重定向路由
const redirectRoute = {
  path: '/redirect',
  name: 'Redirect',
  component: () => import('@/views/Redirect.vue'),
  meta: { requiresAuth: true }
}

// 默认路由
const defaultRoute = {
  path: '/',
  redirect: '/redirect'
}

// 404路由
const notFoundRoute = {
  path: '/:pathMatch(.*)*',
  redirect: '/login'
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...publicRoutes,
    redirectRoute,
    ...adminRoutes,
    ...auditorRoutes,
    ...userRoutes,
    defaultRoute,
    notFoundRoute
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 基于RAG的个性化学习推荐系统`
  }

  // 检查是否需要登录
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
    return
  }

  // 如果已登录且访问登录页，跳转到重定向页
  if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/redirect')
    return
  }

  // 检查角色权限
  if (to.meta.allowedRoles && !to.meta.allowedRoles.includes(userStore.roleId)) {
    next('/redirect')
    return
  }

  next()
})

export default router