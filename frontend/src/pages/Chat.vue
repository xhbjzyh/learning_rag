<template>
  <div class="chat-page">
    <el-card class="chat-container">
      <div class="chat-box" ref="chatBoxRef">
        <div v-for="(item, index) in chatList" :key="index" class="chat-item">
          <div v-if="item.role === 'user'" class="chat-user">
            <div class="chat-content">{{ item.content }}</div>
            <div class="chat-avatar">我</div>
          </div>
          <div v-else class="chat-ai">
            <div class="chat-avatar">AI</div>
            <div class="chat-content">{{ item.content }}</div>
          </div>
        </div>
        <div v-if="loading" class="loading-text">AI 思考中...</div>
      </div>

      <div class="input-box">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="请输入你的问题"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSend"
          style="margin-top: 10px"
        >
          发送问题
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const chatBoxRef = ref(null)
const question = ref('')
const loading = ref(false)
const chatList = ref([
  { role: 'ai', content: '你好！我是 RAG 智能助手，有什么可以帮你的？' }
])

const handleSend = async () => {
  const userQuestion = question.value.trim()
  if (!userQuestion) {
    ElMessage.warning('请输入问题')
    return
  }

  chatList.value.push({ role: 'user', content: userQuestion })
  question.value = ''
  loading.value = true

  try {
    // 🔥 适配修改后的request.js，直接取res.data.answer
    const res = await request.post('/rag/answer', null, {
      params: { query: userQuestion }
    })
    console.log('后端返回：', res)
    const answer = res?.data?.answer || '抱歉，我无法回答这个问题'
    chatList.value.push({ role: 'ai', content: answer })
  } catch (err) {
    console.error(err)
    ElMessage.error('问答失败，请重试')
  } finally {
    loading.value = false
    nextTick(() => {
      chatBoxRef.value?.scrollTo(0, chatBoxRef.value.scrollHeight)
    })
  }
}

onMounted(() => {
  nextTick(() => {
    chatBoxRef.value?.scrollTo(0, chatBoxRef.value.scrollHeight)
  })
})
</script>

<style scoped>
.chat-page {
  max-width: 1000px;
  margin: 0 auto;
}
.chat-container {
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}
.chat-box {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 10px;
}
.chat-item {
  margin-bottom: 20px;
  display: flex;
}
.chat-user {
  justify-content: flex-end;
}
.chat-ai {
  justify-content: flex-start;
}
.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 10px;
  font-weight: bold;
  flex-shrink: 0;
}
.chat-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  line-height: 1.8;
}
.chat-user .chat-content {
  background: #409eff;
  color: #fff;
}
.loading-text {
  text-align: center;
  color: #909399;
  padding: 10px;
}
.input-box {
  padding: 10px;
}
</style>