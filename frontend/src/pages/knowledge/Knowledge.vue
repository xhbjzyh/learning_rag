<template>
  <div class="knowledge-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-button type="primary" @click="handleSyncAll">全量同步到向量库</el-button>
        </div>
      </template>

      <el-table :data="knowledgeList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="知识点标题" width="250" />
        <el-table-column prop="content" label="内容摘要" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" type="primary" @click="handleSyncOne(scope.row.id)">
              同步到向量库
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const knowledgeList = ref([])
const loading = ref(false)

// 获取知识点列表
const getKnowledgeList = async () => {
  loading.value = true
  try {
    const res = await request.get('/rag/points/list')
    knowledgeList.value = res.data || []
  } catch (err) {
    console.error(err)
    ElMessage.error('获取知识点列表失败')
  } finally {
    loading.value = false
  }
}

// 同步单个知识点
const handleSyncOne = async (id) => {
  try {
    await request.post(`/rag/sync/point/${id}`)
    ElMessage.success('同步成功')
    await getKnowledgeList() // 刷新列表
  } catch (err) {
    console.error(err)
    ElMessage.error('同步失败')
  }
}

// 全量同步
const handleSyncAll = async () => {
  try {
    await request.post('/rag/sync/all')
    ElMessage.success('全量同步成功')
    await getKnowledgeList() // 刷新列表
  } catch (err) {
    console.error(err)
    ElMessage.error('全量同步失败')
  }
}

onMounted(() => {
  getKnowledgeList()
})
</script>

<style scoped>
.knowledge-page {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>