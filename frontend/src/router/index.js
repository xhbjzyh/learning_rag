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

// 🔥 确保这里只有一个 createRouter 和 export default
const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 👇 放在最前面，Vue优先匹配这个根路由
    {
      path: '/course-detail/:id',
      name: 'StandaloneCourseDetail',
      component: () => import('@/views/admin/CourseDetail.vue'),
      // 🔥 关键：不设置 allowedRoles，不触发管理员权限校验
      meta: {
        title: '课程详情',
        requiresAuth: true // 只需要登录，不需要管理员角色校验
      }
    },

    ...publicRoutes,
    redirectRoute,
    ...adminRoutes,
    ...auditorRoutes,
    ...userRoutes,
    defaultRoute,
    notFoundRoute
  ]
})

// 路由守卫（精简版）
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.title) {
    document.title = `${to.meta.title} - 基于RAG的个性化学习推荐系统`
  }
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
    return
  }
  if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/redirect')
    return
  }
  next()
})

// 🔥 确保文件末尾只有这一个 export default！
export default router