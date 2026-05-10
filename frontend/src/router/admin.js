export default [
  {
    path: '/admin',
    component: () => import('@/components/common/Layout.vue'),
    meta: { requiresAuth: true, allowedRoles: [1] },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理员仪表盘' }
      },
      {
        path: 'user-manage',
        name: 'UserManage',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'auditor-manage',
        name: 'AuditorManage',
        component: () => import('@/views/admin/AuditorManage.vue'),
        meta: { title: '审核员管理' }
      },
      {
        path: 'content-global',
        name: 'ContentGlobal',
        component: () => import('@/views/admin/ContentGlobal.vue'),
        meta: { title: '内容全局管理' }
      },
      {
        path: 'course-manage',
        name: 'CourseManage',
        component: () => import('@/views/admin/CourseManage.vue'),
        meta: { title: '课程管理' }
      },
      // ✅ 课程详情路由（标准嵌套，无任何错误）
      {
        path: 'course-detail/:id',
        name: 'CourseDetail',
        component: () => import('@/views/admin/CourseDetail.vue'),
        meta: {
          title: '课程详情',
          allowedRoles: [1],
          requiresAuth: true
        }
      },
      {
        path: 'audit-manage',
        name: 'AuditManage',
        component: () => import('@/views/admin/AuditManage.vue'),
        meta: { title: '审核管理' }
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('@/views/admin/SystemConfig.vue'),
        meta: { title: '系统配置' }
      },
      {
        path: 'system-audit',
        name: 'SystemAudit',
        component: () => import('@/views/admin/SystemAudit.vue'),
        meta: { title: '系统审计' }
      }
    ]
  }
]