<template>
  <div class="dashboard-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="data-card">
          <div class="card-content">
            <div class="card-num">{{ statData.knowledge_count }}</div>
            <div class="card-label">知识库总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="data-card">
          <div class="card-content">
            <div class="card-num">{{ statData.document_count }}</div>
            <div class="card-label">文档总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="data-card">
          <div class="card-content">
            <div class="card-num">{{ statData.chat_count }}</div>
            <div class="card-label">对话次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="data-card">
          <div class="card-content">
            <div class="card-num">{{ statData.user_count }}</div>
            <div class="card-label">系统用户数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <div style="text-align: center; padding: 40px 0;">
        <h2>🎉 欢迎使用基于RAG的个性化学习系统</h2>
        <p style="margin: 20px 0; font-size: 16px; color: #666;">
          当前登录用户：{{ userStore.userInfo.username }}
        </p>
        <el-row :gutter="20" justify="center">
          <el-col>
            <el-button type="primary" size="large" @click="goToKnowledge">
              去管理知识库
            </el-button>
          </el-col>
          <el-col>
            <el-button type="success" size="large" @click="goToChat">
              开始对话问答
            </el-button>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const statData = ref({
  user_count: 0,
  knowledge_count: 0,
  document_count: 0,
  chat_count: 0
})

const getStatData = async () => {
  try {
    const res = await request.get('/user/stat/dashboard')
    statData.value = res.data
  } catch (err) {
    console.log(err)
  }
}

onMounted(() => {
  getStatData()
})

const goToKnowledge = () => router.push('/knowledge')
const goToChat = () => router.push('/chat')
</script>

<style scoped lang="scss">
.dashboard-page {
  .data-card {
    .card-content {
      text-align: center;
      .card-num {
        font-size: 36px;
        font-weight: 600;
        color: #409eff;
      }
      .card-label {
        font-size: 14px;
        color: #666;
      }
    }
  }
}
</style>