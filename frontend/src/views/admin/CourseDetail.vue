<template>
  <div class="course-content-wrapper">
    <div class="page-header">
      <h2>课程内容管理 - 课程ID：{{ courseId }}</h2>
      <el-divider />
    </div>

    <!-- 所有el-tab-pane必须放在el-tabs内部 -->
    <el-tabs v-model="activeTab" class="content-tabs">
      <!-- 视频管理 -->
      <el-tab-pane label="视频资料管理" name="video">
        <VideoManager :course-id="courseId" ref="videoRef" />
      </el-tab-pane>

      <!-- 文档管理 -->
      <el-tab-pane label="文档资料管理" name="document">
        <DocumentManager :course-id="courseId" ref="docRef" />
      </el-tab-pane>

      <!-- 习题管理 -->
      <el-tab-pane label="习题管理" name="question">
        <QuestionManager :course-id="courseId" ref="questionRef" />
      </el-tab-pane>

      <!-- ✅ 知识点管理：放在el-tabs内部，使用正确的组件 -->
      <el-tab-pane label="知识点管理" name="knowledge">
        <KnowledgeManagement :course-id="courseId" ref="knowledgeRef" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
// 导入的组件必须在模板中使用，否则会有警告
import KnowledgeManagement from './components/KnowledgeManagement.vue'
import VideoManager from './components/VideoManager.vue'
import DocumentManager from './components/DocumentManager.vue'
import QuestionManager from './components/QuestionManager.vue'

const route = useRoute()
const courseId = ref(route.params.id || 0)
const activeTab = ref('video')

// ✅ ref变量名与模板完全对应
const videoRef = ref(null)
const docRef = ref(null)
const questionRef = ref(null)
const knowledgeRef = ref(null)

// 页面初始化时，加载默认tab的列表
onMounted(() => {
  videoRef.value?.getList()
})

// 暴露方法给父组件（可选，用于刷新所有tab数据）
defineExpose({
  refreshAll: () => {
    videoRef.value?.getList()
    docRef.value?.getList()
    questionRef.value?.getList()
    knowledgeRef.value?.getList()
  }
})
</script>

<style scoped>
.course-content-wrapper {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 100px);
}
.page-header {
  margin-bottom: 20px;
}
</style>