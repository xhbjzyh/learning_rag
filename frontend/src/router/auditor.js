export default [
  {
    path: '/auditor',
    component: () => import('@/components/common/Layout.vue'),
    meta: { requiresAuth: true, allowedRoles: [1, 2] },
    children: [
      {
        path: '',
        redirect: '/auditor/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AuditorDashboard',
        component: () => import('@/views/auditor/Dashboard.vue'),
        meta: { title: '审核员仪表盘' }
      },
      {
        path: 'audit-workbench',
        name: 'AuditWorkbench',
        component: () => import('@/views/auditor/AuditWorkbench.vue'),
        meta: { title: '审核工作台' }
      },
      {
        path: 'public-content',
        name: 'AuditorPublicContent',
        component: () => import('@/views/auditor/PublicContent.vue'),
        meta: { title: '公共内容查看' }
      },
      {
        path: 'personal',
        name: 'AuditorPersonal',
        component: () => import('@/views/auditor/Personal.vue'),
        meta: { title: '个人工作台' }
      }
    ]
  }
]