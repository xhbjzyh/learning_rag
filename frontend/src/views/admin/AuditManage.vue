<template>
  <div class="audit-manage">
    <h2 class="page-title">文档公开申请审核</h2>

    <!-- 审核统计卡片 -->
    <el-row :gutter="20" class="stats-row" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_pending }}</div>
          <div class="stat-label">待审核申请</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_passed }}</div>
          <div class="stat-label">已通过申请</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_rejected }}</div>
          <div class="stat-label">已拒绝申请</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ stats.total_apply }}</div>
          <div class="stat-label">总申请数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card style="margin-bottom: 20px;">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="审核状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable @change="loadAuditList">
            <el-option label="待审核" :value="2" />
            <el-option label="已通过" :value="1" />
            <el-option label="已拒绝" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAllData">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 审核列表 -->
    <el-card>
      <el-table :data="auditList" border stripe v-loading="loading">
        <el-table-column prop="apply_id" label="申请ID" width="80" />
        <el-table-column prop="doc_title" label="文档标题" min-width="200" />
        <el-table-column prop="apply_username" label="申请人" width="120" />
        <el-table-column label="审核人" width="120">
          <template #default="scope">
            {{ scope.row.audit_username || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row)" effect="dark">
              {{ getStatusText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="申请时间" width="180" />
        <el-table-column prop="audit_time" label="审核时间" width="180">
          <template #default="scope">
            {{ scope.row.audit_time || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <template v-if="isPending(scope.row)">
              <el-button
                type="success"
                size="small"
                :loading="passLoadingIds.includes(scope.row.apply_id)"
                @click="handlePass(scope.row)"
              >
                通过
              </el-button>
              <el-button
                type="danger"
                size="small"
                :loading="rejectLoadingIds.includes(scope.row.apply_id)"
                @click="handleReject(scope.row)"
              >
                拒绝
              </el-button>
            </template>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 拒绝原因弹窗 -->
    <el-dialog
      v-model="rejectDialogVisible"
      title="拒绝申请"
      width="500px"
    >
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input
            v-model="rejectForm.remark"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝原因"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject" :loading="submitRejectLoading">
          确认拒绝
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import adminApi from '@/api/admin'

// 状态
const loading = ref(false)
const auditList = ref([])
const passLoadingIds = ref([])
const rejectLoadingIds = ref([])
const rejectDialogVisible = ref(false)
const submitRejectLoading = ref(false)
const currentRejectRow = ref(null)

// 统计数据
const stats = ref({
  total_pending: 0,
  total_passed: 0,
  total_rejected: 0,
  total_apply: 0
})

// 筛选表单
const filterForm = ref({
  status: null
})

// 拒绝表单
const rejectForm = ref({
  remark: ''
})

// 状态辅助函数（完全匹配后端返回字段）
const isPending = (row) => {
  // 待审核判断：没有apply_status 或 apply_status为null
  return !row.apply_status
}

const getStatusType = (row) => {
  if (isPending(row)) return 'warning'
  // apply_status: 1=已通过, 2=已拒绝
  return row.apply_status === 1 ? 'success' : 'danger'
}

const getStatusText = (row) => {
  if (isPending(row)) return '待审核'
  // 优先使用后端返回的status_text
  if (row.status_text) return row.status_text
  return row.apply_status === 1 ? '已通过' : '已拒绝'
}

// 加载所有数据（统计+列表）
const loadAllData = async () => {
  loading.value = true
  try {
    // 并行请求统计和列表
    const [statsRes, pendingRes, historyRes] = await Promise.all([
      adminApi.getAuditStats(),
      adminApi.getPendingAuditList(),
      adminApi.getAuditHistory()
    ])

    // 更新统计数据
    stats.value = statsRes.data || stats.value

    // 合并待审核和历史记录
    let allList = [...(pendingRes.data || []), ...(historyRes.data || [])]

    // 前端筛选
    if (filterForm.value.status !== null) {
      if (filterForm.value.status === 2) {
        // 筛选待审核
        allList = allList.filter(item => isPending(item))
      } else if (filterForm.value.status === 1) {
        // 筛选已通过
        allList = allList.filter(item => item.apply_status === 1)
      } else if (filterForm.value.status === 3) {
        // 筛选已拒绝
        allList = allList.filter(item => item.apply_status === 2)
      }
    }

    // 按申请时间倒序排列
    allList.sort((a, b) => new Date(b.create_time) - new Date(a.create_time))

    auditList.value = allList
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败，请刷新重试')
  } finally {
    loading.value = false
  }
}

// 只加载列表（用于筛选）
const loadAuditList = () => {
  loadAllData()
}

// 审核通过（添加前置校验）
const handlePass = async (row) => {
  // 前置校验：如果已经审核过了，直接提示
  if (!isPending(row)) {
    ElMessage.warning('该申请已经审核过了')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认通过文档《${row.doc_title}》的公开申请？`,
      '审核通过',
      {
        confirmButtonText: '确认通过',
        cancelButtonText: '取消',
        type: 'success'
      }
    )

    passLoadingIds.value.push(row.apply_id)

    // 调用接口：audit_status=1表示通过
    await adminApi.auditApply(row.apply_id, 1, '审核通过')

    ElMessage.success('审核通过成功')

    // 重新加载所有数据
    loadAllData()

  } catch (error) {
    if (error !== 'cancel') {
      console.error('审核通过失败:', error)
      ElMessage.error(error.response?.data?.msg || '审核通过失败')
    }
  } finally {
    passLoadingIds.value = passLoadingIds.value.filter(id => id !== row.apply_id)
  }
}

// 审核拒绝（打开弹窗）
const handleReject = (row) => {
  currentRejectRow.value = row
  rejectForm.value.remark = ''
  rejectDialogVisible.value = true
}

// 提交拒绝（添加前置校验）
const submitReject = async () => {
  if (!rejectForm.value.remark.trim()) {
    ElMessage.warning('请输入拒绝原因')
    return
  }

  const row = currentRejectRow.value

  // 前置校验：如果已经审核过了，直接提示
  if (!isPending(row)) {
    ElMessage.warning('该申请已经审核过了')
    rejectDialogVisible.value = false
    return
  }

  submitRejectLoading.value = true

  try {
    // 调用接口：audit_status=2表示驳回
    await adminApi.auditApply(row.apply_id, 2, rejectForm.value.remark)

    ElMessage.success('已拒绝该申请')
    rejectDialogVisible.value = false

    // 重新加载所有数据
    loadAllData()

  } catch (error) {
    console.error('拒绝申请失败:', error)
    ElMessage.error(error.response?.data?.msg || '拒绝申请失败')
  } finally {
    submitRejectLoading.value = false
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.audit-manage { padding: 20px; }
.page-title { margin-bottom: 20px; font-size: 24px; font-weight: 600; color: #303133; }
.stats-row { margin-bottom: 20px; }
.stat-card { text-align: center; }
.stat-value { font-size: 28px; font-weight: bold; margin-bottom: 5px; color: #303133; }
.stat-label { font-size: 14px; color: #909399; }
</style>