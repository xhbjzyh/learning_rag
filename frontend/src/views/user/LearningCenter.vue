<template>
  <div class="learning-center">
    <div class="page-header">
      <h2 class="page-title">学习中心</h2>
      <el-button type="primary" :icon="Notebook" @click="goToWrongBook">
        我的错题本
      </el-button>
    </div>

    <!-- 顶部搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索课程..."
        style="width: 400px"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
    </div>

    <!-- 三级分类筛选栏 -->
    <div class="category-filter">
      <div class="filter-row">
        <span class="filter-label">课程分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level1Categories"
            :key="cat.id"
            :type="selectedLevel1 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel1Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>

      <div v-if="level2Categories.length > 0" class="filter-row">
        <span class="filter-label">二级分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level2Categories"
            :key="cat.id"
            :type="selectedLevel2 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel2Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>

      <div v-if="level3Categories.length > 0" class="filter-row">
        <span class="filter-label">三级分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level3Categories"
            :key="cat.id"
            :type="selectedLevel3 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel3Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 课程卡片列表 -->
    <div class="course-list">
      <div v-if="courseList.length === 0 && !loading" class="empty-data">
        <el-empty description="暂无课程" />
      </div>

      <el-skeleton v-if="loading" :rows="3" animated />

      <el-card
        v-else
        v-for="course in courseList"
        :key="course.id"
        class="course-card"
        shadow="hover"
        @click="goToCourseDetail(course.id)"
      >
        <div class="card-content">
          <div class="card-cover">
            <img :src="course.cover_url || defaultCover" :alt="course.title" />
          </div>
          <div class="card-info">
            <h3 class="card-title">{{ course.title }}</h3>
            <p class="card-desc">{{ course.description || '暂无简介' }}</p>
            <div class="card-meta">
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ course.lecturer || '未知讲师' }}
              </span>
              <span class="meta-item">
                <el-icon><View /></el-icon>
                {{ course.view_count }} 次学习
              </span>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 40]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="loadCourseList"
      @size-change="handleSizeChange"
      class="pagination"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, User, View, Notebook } from '@element-plus/icons-vue'
import courseApi from '@/api/user/course.js'

const router = useRouter()

// 默认封面
const defaultCover = 'https://via.placeholder.com/300x200?text=课程封面'

// 搜索
const searchKeyword = ref('')

// 分类
const allCategories = ref([])
const selectedLevel1 = ref(null)
const selectedLevel2 = ref(null)
const selectedLevel3 = ref(null)

// 课程列表
const courseList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 计算属性：一级分类
const level1Categories = computed(() => {
  return allCategories.value.filter(cat => cat.level === 1)
})

// 计算属性：二级分类
const level2Categories = computed(() => {
  if (!selectedLevel1.value) return []
  const level1 = allCategories.value.find(cat => cat.id === selectedLevel1.value)
  return level1?.children || []
})

// 计算属性：三级分类
const level3Categories = computed(() => {
  if (!selectedLevel2.value) return []
  const level2 = allCategories.value.find(cat => id === selectedLevel2.value)
  return level2?.children || []
})

// 加载分类
const loadCategories = async () => {
  try {
    const res = await courseApi.getCategories()
    if (res && res.code === 0) {
      allCategories.value = res.data
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

// 加载课程列表
const loadCourseList = async () => {
  loading.value = true
  try {
    const categoryId = selectedLevel3.value || selectedLevel2.value || selectedLevel1.value
    const res = await courseApi.getCourseList({
      category_id: categoryId,
      keyword: searchKeyword.value,
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (res && res.code === 0) {
      // ✅ 重点：后端返回的列表字段以实际接口返回为准（Swagger测试后确认）
      courseList.value = res.data.items || res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载课程列表失败:', error)
    ElMessage.error('加载课程列表失败')
  } finally {
    loading.value = false
  }
}

// 选择一级分类
const selectLevel1Category = (cat) => {
  selectedLevel1.value = selectedLevel1.value === cat.id ? null : cat.id
  selectedLevel2.value = null
  selectedLevel3.value = null
  currentPage.value = 1
  loadCourseList()
}

// 选择二级分类
const selectLevel2Category = (cat) => {
  selectedLevel2.value = selectedLevel2.value === cat.id ? null : cat.id
  selectedLevel3.value = null
  currentPage.value = 1
  loadCourseList()
}

// 选择三级分类
const selectLevel3Category = (cat) => {
  selectedLevel3.value = selectedLevel3.value === cat.id ? null : cat.id
  currentPage.value = 1
  loadCourseList()
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadCourseList()
}

// 分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadCourseList()
}

// 跳转到课程详情
const goToCourseDetail = (courseId) => {
  router.push(`/user/course/${courseId}`)
}

// 跳转到错题本
const goToWrongBook = () => {
  router.push('/user/wrong-question-book')
}

onMounted(() => {
  loadCategories()
  loadCourseList()
})
</script>

<style scoped>
.learning-center {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.search-bar {
  margin-bottom: 24px;
}

.category-filter {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-label {
  font-size: 14px;
  color: #666;
  width: 80px;
  flex-shrink: 0;
  padding-top: 4px;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.filter-tag:hover {
  transform: translateY(-1px);
}

.course-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.course-card {
  cursor: pointer;
  transition: all 0.3s;
}

.course-card:hover {
  transform: translateY(-4px);
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-cover {
  width: 100%;
  height: 180px;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 16px;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  flex: 1;
}

.card-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  margin: 0 0 12px;
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #999;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.empty-data {
  grid-column: 1 / -1;
  padding: 60px 0;
}

.pagination {
  display: flex;
  justify-content: center;
}
</style>