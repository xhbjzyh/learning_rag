<template>
  <div class="system-config">
    <h2 class="page-title">系统配置</h2>
    <el-card>
      <el-form :model="configForm" label-width="120px" style="max-width: 600px;">
        <el-form-item label="系统名称">
          <el-input v-model="configForm.system_name" placeholder="请输入系统名称" />
        </el-form-item>
        <el-form-item label="允许上传文件类型">
          <el-input v-model="configForm.allowed_file_types" placeholder="请输入允许的文件类型，用逗号分隔" />
        </el-form-item>
        <el-form-item label="单个文件最大大小(MB)">
          <el-input-number v-model="configForm.max_file_size" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="是否开启注册">
          <el-switch v-model="configForm.enable_register" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const configForm = ref({
  system_name: 'RAG学习系统',
  allowed_file_types: 'pdf,doc,docx,txt',
  max_file_size: 100,
  enable_register: true
})

const saveConfig = () => {
  ElMessage.success('配置保存成功')
}
</script>

<style scoped>
.system-config { padding: 20px; }
.page-title { margin-bottom: 20px; font-size: 24px; font-weight: 600; color: #303133; }
</style>