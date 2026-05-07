export default [
  {
    path: '/user',
    component: () => import('@/components/common/Layout.vue'),
    meta: { requiresAuth: true, allowedRoles: [1, 2, 3] },
    children: [
      {
        path: '',
        redirect: '/user/dashboard'
      },
      {
        path: 'dashboard',
        name: 'UserDashboard',
        component: () => import('@/views/user/Dashboard.vue'),
        meta: { title: '用户仪表盘' }
      },
      {
        path: 'private-knowledge',
        name: 'PrivateKnowledge',
        component: () => import('@/views/user/PrivateKnowledge.vue'),
        meta: { title: '私有知识库' }
      },
      {
        path: 'public-content',
        name: 'PublicContent',
        component: () => import('@/views/user/PublicContent.vue'),
        meta: { title: '公共内容' }
      },
      {
        path: 'content-apply',
        name: 'ContentApply',
        component: () => import('@/views/user/ContentApply.vue'),
        meta: { title: '内容公开申请' }
      },
      {
        path: 'learning-center',
        name: 'LearningCenter',
        component: () => import('@/views/user/LearningCenter.vue'),
        meta: { title: '学习中心' }
      },
      {
        path: 'personal-recommend',
        name: 'PersonalRecommend',
        component: () => import('@/views/user/PersonalRecommend.vue'),
        meta: { title: '个性化推荐' }
      },
      {
        path: 'user-profile',
        name: 'UserProfile',
        component: () => import('@/views/user/UserProfile.vue'),
        meta: { title: '用户画像' }
      },
      {
        path: 'rag-chat',
        name: 'RAGChat',
        component: () => import('@/views/user/RAGChat.vue'),
        meta: { title: 'RAG问答' }
      },
      {
        path: 'personal-center',
        name: 'PersonalCenter',
        component: () => import('@/views/user/PersonalCenter.vue'),
        meta: { title: '个人中心' }
      }
    ]
  }
]