<template>
  <div class="rag-chat">
    <div class="chat-container">
      <!-- 聊天消息区 -->
      <div class="chat-messages" ref="messagesRef">
        <el-empty v-if="messages.length === 0" description="开始你的RAG问答之旅吧！" />

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
            <el-icon v-else :size="24" color="#409EFF"><Platform /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble" v-html="msg.content"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>

        <!-- 🔥 流式输出中的消息 -->
        <div v-if="isStreaming" class="message-item assistant">
          <div class="message-avatar">
            <el-icon :size="24" color="#409EFF"><Platform /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              {{ streamingContent }}
              <span class="cursor">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 公共/私有切换开关 -->
      <div class="kb-switch">
        <el-radio-group v-model="kbType" size="small">
          <el-radio label="private">私有知识库</el-radio>
          <el-radio label="public">公共知识库</el-radio>
        </el-radio-group>
        <el-button type="text" @click="handleClearHistory" :disabled="isStreaming">
          清除历史
        </el-button>
      </div>

      <!-- 输入区 -->
      <div class="chat-input">
        <el-input
          v-model="query"
          type="textarea"
          :rows="3"
          placeholder="请输入你的问题..."
          :disabled="isStreaming"
          @keyup.ctrl.enter="handleSend"
        />
        <div class="input-actions">
          <span class="input-tip">按 Ctrl+Enter 发送</span>
          <el-button
            type="primary"
            :loading="isStreaming"
            @click="handleSend"
          >
            {{ isStreaming ? '回答中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import ragApi from '@/api/user/rag'
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Platform } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'

const messagesRef = ref(null)
const query = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const kbType = ref("private")

const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是基于RAG的智能学习助手，支持公共/私有知识库切换~',
    time: formatDate(new Date(), 'HH:mm:ss')
  }
])

// 格式化Markdown内容
const formatContent = (content) => {
  return content
    .replace(/\n/g, '<br>')
    .replace(/### (.*?)(<br>|$)/g, '<h3 style="margin:10px 0;font-size:16px;color:#303133;">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#303133;">$1</strong>')
    .replace(/- (.*?)(<br>|$)/g, '<li style="margin-left:20px;list-style-type:disc;">$1</li>')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 🔥 新增：清除对话历史
const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除对话历史吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await ragApi.clearHistory()
    messages.value = [
      {
        role: 'assistant',
        content: '你好！我是基于RAG的智能学习助手，支持公共/私有知识库切换~',
        time: formatDate(new Date(), 'HH:mm:ss')
      }
    ]
    ElMessage.success('对话历史已清除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除历史失败:', error)
      ElMessage.error('清除历史失败')
    }
  }
}

// 🔥 修改：流式发送消息
const handleSend = async () => {
  if (!query.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  if (isStreaming.value) return

  // 添加用户消息
  const userMessage = {
    role: 'user',
    content: query.value,
    time: formatDate(new Date(), 'HH:mm:ss')
  }
  messages.value.push(userMessage)

  const userQuery = query.value
  query.value = ''
  isStreaming.value = true
  streamingContent.value = ''

  scrollToBottom()

  try {
    // 🔥 使用正确的流式接口路径
    const token = localStorage.getItem('rag_token')
    const response = await fetch(
      `/api/user/rag/answer/stream?query=${encodeURIComponent(userQuery)}&kb_type=${kbType.value}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )

    if (!response.ok) throw new Error('请求失败')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      streamingContent.value += chunk
      scrollToBottom()
    }

    // 流式结束，添加完整消息
    if (streamingContent.value) {
      const assistantMessage = {
        role: 'assistant',
        content: formatContent(streamingContent.value),
        time: formatDate(new Date(), 'HH:mm:ss')
      }
      messages.value.push(assistantMessage)
    }

  } catch (error) {
    console.error('流式问答失败:', error)
    ElMessage.error('问答失败，请稍后重试')
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
    scrollToBottom()
  }

}
</script>

<style scoped>
/* 核心修复：层级与布局控制 */
.rag-chat {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  background: #f0f2f5;
}

.chat-container {
  width: 100%;
  max-width: 900px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-height: calc(100% - 200px);
}

.message-item {
  display: flex;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #409EFF;
  color: #fff;
}

.message-content {
  max-width: 70%;
  margin: 0 15px;
}

.message-item.user .message-content {
  text-align: right;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  text-align: left;
}

.message-item.user .message-bubble {
  background: #409EFF;
  color: #fff;
  text-align: right;
}

/* 🔥 新增：光标闪烁动画 */
.cursor {
  display: inline-block;
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.kb-switch {
  padding: 10px 20px;
  border-top: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  z-index: 10;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e6e6e6;
  background: #fff;
  z-index: 10;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-tip {
  font-size: 12px;
  color: #999;
}
</style>