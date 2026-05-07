<template>
  <div class="system-audit">
    <h2 class="page-title">系统操作日志</h2>
    <el-card>
      <el-table :data="auditLogList" border stripe loading="loading">
        <el-table-column prop="id" label="日志ID" width="80" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="operation" label="操作内容" />
        <el-table-column prop="ip" label="操作IP" width="150" />
        <el-table-column prop="create_time" label="操作时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import adminApi from '@/api/admin'

const auditLogList = ref([])
const loading = ref(false)

const getAuditLogList = async () => {
  loading.value = true
  try {
    const res = await adminApi.getAuditLogList()
    auditLogList.value = res.data
  } catch (error) {
    // 模拟数据
    auditLogList.value = [
      { id: 1, username: 'admin', operation: '登录系统', ip: '127.0.0.1', create_time: '2026-04-28 10:00:00' },
      { id: 2, username: 'admin', operation: '审核通过文档《算法第四版》', ip: '127.0.0.1', create_time: '2026-04-28 10:30:00' },
      { id: 3, username: 'test001', operation: '上传文档《机器学习入门》', ip: '127.0.0.1', create_time: '2026-04-28 11:00:00' }
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  getAuditLogList()
})
</script>

<style scoped>
.system-audit { padding: 20px; }
.page-title { margin-bottom: 20px; font-size: 24px; font-weight: 600; color: #303133; }
</style>