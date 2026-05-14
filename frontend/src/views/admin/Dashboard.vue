<template>
  <div class="admin-dashboard">
    <h2 class="page-title">管理员仪表盘</h2>

    <!-- 核心数据统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><el-icon :size="40" color="#409EFF"><User /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">注册用户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><el-icon :size="40" color="#E6A23C"><Document /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pendingAuditCount }}</div>
            <div class="stat-label">待审核申请</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><el-icon :size="40" color="#67C23A"><Files /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.docCount }}</div>
            <div class="stat-label">平台文档总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><el-icon :size="40" color="#909399"><Collection /></el-icon></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.auditorCount }}</div>
            <div class="stat-label">审核员数量</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作入口 -->
    <el-card title="快捷管理入口" class="quick-actions-card">
      <div class="action-buttons">
        <el-button type="primary" @click="$router.push('/admin/user-manage')">
          <el-icon><User /></el-icon> 用户管理
        </el-button>
        <el-button type="warning" @click="$router.push('/admin/audit-manage')">
          <el-icon><Document /></el-icon> 文档审核
        </el-button>
        <el-button type="success" @click="$router.push('/admin/content-global')">
          <el-icon><Files /></el-icon> 全局文档
        </el-button>
        <el-button type="info" @click="$router.push('/admin/auditor-manage')">
          <el-icon><UserFilled /></el-icon> 审核员管理
        </el-button>
      </div>
    </el-card>

    <!-- 最近待审核申请 -->
    <el-card title="待审核公开申请（最近5条）" class="pending-audit-card">
      <el-table :data="pendingAuditList" border size="small" v-if="pendingAuditList.length > 0">
        <el-table-column prop="id" label="申请ID" width="80" />
        <el-table-column prop="doc_title" label="文档标题" />
        <el-table-column prop="username" label="申请人" width="120" />
        <el-table-column prop="create_time" label="申请时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="success" size="small" @click="handlePass(scope.row.id)">通过</el-button>
            <el-button type="danger" size="small" @click="handleReject(scope.row.id)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty description="暂无待审核申请" v-else />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Document, Files, Collection, UserFilled } from '@element-plus/icons-vue'
import adminApi from '@/api/admin'

// 统计数据
const stats = ref({
  userCount: 0,
  pendingAuditCount: 0,
  docCount: 0,
  auditorCount: 0
})

// 待审核列表
const pendingAuditList = ref([])

// 获取统计数据
const getStats = async () => {
  try {
    const res = await adminApi.getDashboardStats()
    if (res.code === 0 && res.data) {
      stats.value.userCount = res.data.user_count || 0
      stats.value.pendingAuditCount = res.data.pending_audit_count || 0
      stats.value.docCount = res.data.doc_count || 0
      stats.value.auditorCount = res.data.auditor_count || 0
      pendingAuditList.value = res.data.recent_pending || []
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

// 审核操作
const handlePass = async (id) => {
  try {
    await ElMessageBox.confirm('确认通过该申请？')
    // TODO: 调用审核通过接口
    ElMessage.success('审核通过')
    getStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleReject = async (id) => {
  try {
    await ElMessageBox.confirm('确认拒绝该申请？')
    // TODO: 调用审核拒绝接口
    ElMessage.success('已拒绝')
    getStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

onMounted(() => {
  getStats()
})
</script>

<style scoped>
.admin-dashboard { padding: 20px; }
.page-title { margin-bottom: 20px; font-size: 24px; font-weight: 600; color: #303133; }
.stats-row { margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 15px; }
.stat-value { font-size: 28px; font-weight: bold; margin-bottom: 5px; }
.stat-label { font-size: 14px; color: #909399; }
.quick-actions-card { margin-bottom: 20px; }
.action-buttons { display: flex; gap: 15px; flex-wrap: wrap; }
.pending-audit-card { min-height: 300px; }
</style>