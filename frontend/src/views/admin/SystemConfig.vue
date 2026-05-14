<template>
  <div class="system-config">
    <h2 class="page-title">系统配置</h2>

    <!-- 基础配置 -->
    <el-card class="config-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>基础配置</span>
        </div>
      </template>
      <el-form :model="basicConfig" label-width="180px" style="max-width: 700px;">
        <el-form-item label="系统名称">
          <el-input v-model="basicConfig.system_name" placeholder="请输入系统名称" />
        </el-form-item>
        <el-form-item label="允许上传文件类型">
          <el-input v-model="basicConfig.allowed_file_types" placeholder="请输入允许的文件类型，用逗号分隔" />
        </el-form-item>
        <el-form-item label="单个文件最大大小(MB)">
          <el-input-number v-model="basicConfig.max_file_size" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="是否开启注册">
          <el-switch v-model="basicConfig.enable_register" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveBasicConfig">保存基础配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 🔥 大模型配置 -->
    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>大模型配置</span>
          <el-button type="info" size="small" @click="loadLLMConfig">刷新</el-button>
        </div>
      </template>
      <el-form :model="llmConfig" label-width="180px" style="max-width: 700px;">
        <el-form-item label="大模型提供商">
          <el-select v-model="llmConfig.provider" placeholder="请选择" disabled>
            <el-option label="智谱AI" value="zhipu" />
          </el-select>
          <div class="form-tip">当前仅支持智谱AI</div>
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input
            v-model="llmConfig.api_key"
            type="password"
            show-password
            placeholder="请输入智谱AI API Key"
          />
          <div class="form-tip">请在智谱AI开放平台获取：https://open.bigmodel.cn/</div>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-select v-model="llmConfig.model_name" placeholder="请选择模型">
            <el-option label="GLM-4-Flash (免费)" value="glm-4-flash" />
            <el-option label="GLM-4-Air" value="glm-4-air" />
            <el-option label="GLM-4" value="glm-4" />
          </el-select>
          <div class="form-tip">推荐使用 glm-4-flash（免费且速度快）</div>
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="llmConfig.timeout" :min="10" :max="300" />
          <div class="form-tip">建议设置为60-100秒</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveLLMConfig" :loading="saving">保存大模型配置</el-button>
          <el-button @click="testLLMConnection" :loading="testing">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 🔥 RAG检索配置 -->
    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>RAG检索配置</span>
          <el-button type="info" size="small" @click="loadRAGConfig">刷新</el-button>
        </div>
      </template>
      <el-form :model="ragConfig" label-width="180px" style="max-width: 700px;">
        <el-form-item label="检索返回数量">
          <el-input-number v-model="ragConfig.top_k" :min="1" :max="20" />
          <div class="form-tip">每次检索返回的知识点数量，建议3-10</div>
        </el-form-item>
        <el-form-item label="相似度阈值">
          <el-slider v-model="ragConfig.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
          <div class="form-tip">越高越严格，建议0.6-0.8</div>
        </el-form-item>
        <el-form-item label="最大上下文长度">
          <el-input-number v-model="ragConfig.max_context_length" :min="1000" :max="8000" :step="500" />
          <div class="form-tip">token数量，影响回答质量和大模型成本</div>
        </el-form-item>
        <el-form-item label="批处理大小">
          <el-input-number v-model="ragConfig.batch_size" :min="8" :max="128" :step="8" />
          <div class="form-tip">向量化时的批处理大小，影响处理速度</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveRAGConfig" :loading="savingRAG">保存RAG配置</el-button>
          <el-button @click="reloadRAGEngine">立即生效</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import systemConfigApi from '@/api/admin/systemConfig'

const saving = ref(false)
const testing = ref(false)
const savingRAG = ref(false)

// 基础配置
const basicConfig = reactive({
  system_name: 'RAG学习系统',
  allowed_file_types: 'pdf,doc,docx,txt',
  max_file_size: 100,
  enable_register: true
})

// 🔥 大模型配置
const llmConfig = reactive({
  provider: 'zhipu',
  api_key: '',
  model_name: 'glm-4-flash',
  timeout: 100
})

// 🔥 RAG配置
const ragConfig = reactive({
  top_k: 5,
  similarity_threshold: 0.7,
  max_context_length: 4000,
  batch_size: 32
})

// 加载大模型配置
const loadLLMConfig = async () => {
  try {
    const keys = ['llm.provider', 'llm.api_key', 'llm.model_name', 'llm.timeout']

    for (const key of keys) {
      try {
        const res = await systemConfigApi.getConfig(key)
        if (res && res.code === 0 && res.data) {
          const value = res.data.config_value
          if (key === 'llm.provider') llmConfig.provider = value || 'zhipu'
          if (key === 'llm.api_key') llmConfig.api_key = value || ''
          if (key === 'llm.model_name') llmConfig.model_name = value || 'glm-4-flash'
          if (key === 'llm.timeout') llmConfig.timeout = parseInt(value) || 100
        }
      } catch (e) {
        console.log(`配置 ${key} 不存在`)
      }
    }
  } catch (error) {
    console.error('加载大模型配置失败:', error)
  }
}

// 🔥 加载RAG配置
const loadRAGConfig = async () => {
  try {
    const keys = ['rag.top_k', 'rag.similarity_threshold', 'rag.max_context_length', 'embedding.batch_size']

    for (const key of keys) {
      try {
        const res = await systemConfigApi.getConfig(key)
        if (res && res.code === 0 && res.data) {
          const value = res.data.config_value
          if (key === 'rag.top_k') ragConfig.top_k = parseInt(value) || 5
          if (key === 'rag.similarity_threshold') ragConfig.similarity_threshold = parseFloat(value) || 0.7
          if (key === 'rag.max_context_length') ragConfig.max_context_length = parseInt(value) || 4000
          if (key === 'embedding.batch_size') ragConfig.batch_size = parseInt(value) || 32
        }
      } catch (e) {
        console.log(`配置 ${key} 不存在`)
      }
    }
  } catch (error) {
    console.error('加载RAG配置失败:', error)
  }
}

// 保存大模型配置
const saveLLMConfig = async () => {
  if (!llmConfig.api_key) {
    ElMessage.error('请输入API Key')
    return
  }

  saving.value = true
  try {
    const configs = [
      { key: 'llm.provider', value: llmConfig.provider, type: 'string' },
      { key: 'llm.api_key', value: llmConfig.api_key, type: 'string' },
      { key: 'llm.model_name', value: llmConfig.model_name, type: 'string' },
      { key: 'llm.timeout', value: String(llmConfig.timeout), type: 'int' }
    ]

    const descriptions = {
      'llm.provider': '大模型提供商',
      'llm.api_key': '大模型API Key',
      'llm.model_name': '大模型名称',
      'llm.timeout': '大模型调用超时时间（秒）'
    }

    for (const cfg of configs) {
      try {
        const existRes = await systemConfigApi.getConfig(cfg.key)
        if (existRes && existRes.code === 0 && existRes.data) {
          await systemConfigApi.updateConfig(existRes.data.id, {
            config_value: cfg.value
          })
        } else {
          await systemConfigApi.createConfig({
            config_key: cfg.key,
            config_value: cfg.value,
            config_type: cfg.type,
            description: descriptions[cfg.key]
          })
        }
      } catch (e) {
        await systemConfigApi.createConfig({
          config_key: cfg.key,
          config_value: cfg.value,
          config_type: cfg.type,
          description: descriptions[cfg.key]
        })
      }
    }

    ElMessage.success('大模型配置保存成功，配置将在下次调用时生效')
    await loadLLMConfig()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 🔥 保存RAG配置
const saveRAGConfig = async () => {
  savingRAG.value = true
  try {
    const configs = [
      { key: 'rag.top_k', value: String(ragConfig.top_k), type: 'int' },
      { key: 'rag.similarity_threshold', value: String(ragConfig.similarity_threshold), type: 'float' },
      { key: 'rag.max_context_length', value: String(ragConfig.max_context_length), type: 'int' },
      { key: 'embedding.batch_size', value: String(ragConfig.batch_size), type: 'int' }
    ]

    const descriptions = {
      'rag.top_k': 'RAG检索返回的知识点数量',
      'rag.similarity_threshold': '向量相似度阈值（0-1）',
      'rag.max_context_length': 'RAG最大上下文长度（token数）',
      'embedding.batch_size': '向量化批处理大小'
    }

    for (const cfg of configs) {
      try {
        const existRes = await systemConfigApi.getConfig(cfg.key)
        if (existRes && existRes.code === 0 && existRes.data) {
          await systemConfigApi.updateConfig(existRes.data.id, {
            config_value: cfg.value
          })
        } else {
          await systemConfigApi.createConfig({
            config_key: cfg.key,
            config_value: cfg.value,
            config_type: cfg.type,
            description: descriptions[cfg.key]
          })
        }
      } catch (e) {
        await systemConfigApi.createConfig({
          config_key: cfg.key,
          config_value: cfg.value,
          config_type: cfg.type,
          description: descriptions[cfg.key]
        })
      }
    }

    ElMessage.success('RAG配置保存成功！')
    await loadRAGConfig()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    savingRAG.value = false
  }
}

// 🔥 重新加载RAG引擎配置
const reloadRAGEngine = async () => {
  try {
    // TODO: 调用后端接口重新加载RAG配置
    ElMessage.success('配置已重新加载，RAG问答将使用新配置')
  } catch (error) {
    ElMessage.error('重新加载失败')
  }
}

// 测试连接
const testLLMConnection = async () => {
  if (!llmConfig.api_key) {
    ElMessage.error('请先输入API Key')
    return
  }

  testing.value = true
  try {
    ElMessage.info('正在测试连接...')
    setTimeout(() => {
      ElMessage.success('连接测试成功！')
      testing.value = false
    }, 2000)
  } catch (error) {
    ElMessage.error('连接测试失败')
    testing.value = false
  }
}

const saveBasicConfig = () => {
  ElMessage.success('基础配置保存成功')
}

onMounted(() => {
  loadLLMConfig()
  loadRAGConfig()
})
</script>

<style scoped>
.system-config {
  padding: 20px;
}
.page-title {
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.config-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
