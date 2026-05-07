<template>
  <div class="content-global">
    <h2 class="page-title">公共内容管理</h2>

    <el-card>
      <!-- 标签页切换三个模块 -->
      <el-tabs v-model="activeTab" type="card" @tab-change="handleTabChange">
        <!-- 1. 分类管理 -->
        <el-tab-pane label="分类管理" name="category">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" @click="showAddCategoryDialog = true">新增分类</el-button>
          </div>

          <el-table :data="categoryList" border stripe v-loading="categoryLoading">
            <el-table-column prop="id" label="分类ID" width="80" />
            <el-table-column prop="category_name" label="分类名称" />
            <el-table-column prop="description" label="分类描述" />
            <el-table-column prop="create_time" label="创建时间" width="180" />
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="scope">
                <el-button size="small" type="success" @click="viewCategoryKnowledge(scope.row)">
                  查看知识点
                </el-button>
                <el-button size="small" @click="handleEditCategory(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteCategory(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 2. 知识点管理 -->
        <el-tab-pane label="知识点管理" name="knowledge">
          <!-- 🔥 新增：分类筛选栏 -->
          <div class="filter-bar" v-if="selectedCategory">
            <el-alert
              :title="`当前查看：「${selectedCategory.category_name}」分类下的知识点`"
              type="info"
              show-icon
              :closable="true"
              @close="clearCategoryFilter"
              style="margin-bottom: 16px;"
            />
          </div>

          <el-table :data="knowledgeList" border stripe v-loading="knowledgeLoading">
            <el-table-column prop="id" label="知识点ID" width="80" />
            <el-table-column prop="title" label="知识点标题" min-width="200" />
            <el-table-column prop="difficulty" label="难度" width="100" />
            <el-table-column prop="category_name" label="所属分类" width="120" />
            <el-table-column prop="create_time" label="创建时间" width="180" />
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="handleViewKnowledge(scope.row)">查看</el-button>
                <el-button size="small" type="warning" @click="handleEditKnowledge(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteKnowledge(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div style="margin-top: 20px; text-align: center;">
            <el-pagination
              :current-page="knowledgePage"
              :page-size="knowledgeSize"
              :total="knowledgeTotal"
              @current-change="loadKnowledgeList"
              layout="total, prev, pager, next, jumper"
            />
          </div>
        </el-tab-pane>

        <!-- 3. 文档管理 -->
        <el-tab-pane label="文档管理" name="document">
          <!-- 筛选栏 -->
          <el-form :inline="true" :model="documentFilter" style="margin-bottom: 15px;">
            <el-form-item label="分类">
              <el-select v-model="documentFilter.category_id" placeholder="全部分类" clearable>
                <el-option
                  v-for="cat in categoryList"
                  :key="cat.id"
                  :label="cat.category_name"
                  :value="cat.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="审核状态">
              <el-select v-model="documentFilter.audit_status" placeholder="全部状态" clearable>
                <el-option label="未提交" :value="0" />
                <el-option label="已通过" :value="1" />
                <el-option label="待审核" :value="2" />
                <el-option label="已拒绝" :value="3" />
              </el-select>
            </el-form-item>
            <el-form-item label="公开状态">
              <el-select v-model="documentFilter.is_public" placeholder="全部" clearable>
                <el-option label="公开" :value="true" />
                <el-option label="私有" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadDocumentList">查询</el-button>
              <el-button @click="resetDocumentFilter">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="documentList" border stripe v-loading="documentLoading">
            <el-table-column prop="id" label="文档ID" width="80" />
            <el-table-column prop="title" label="文档标题" min-width="200" />
            <el-table-column prop="category_name" label="分类" width="120" />
            <el-table-column prop="upload_username" label="上传用户" width="120" />
            <el-table-column label="审核状态" width="100">
              <template #default="scope">
                <el-tag :type="getAuditStatusType(scope.row.audit_status)" effect="dark">
                  {{ getAuditStatusText(scope.row.audit_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="公开状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_public ? 'success' : 'info'" effect="dark">
                  {{ scope.row.is_public ? '公开' : '私有' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="上传时间" width="180" />
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="handleDownloadDocument(scope.row)">下载</el-button>
                <el-button size="small" type="danger" @click="handleDeleteDocument(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div style="margin-top: 20px; text-align: center;">
            <el-pagination
              :current-page="documentPage"
              :page-size="documentSize"
              :total="documentTotal"
              @current-change="loadDocumentList"
              layout="total, prev, pager, next, jumper"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ===================== 补全所有弹窗 ===================== -->
    <!-- 新增分类弹窗 -->
    <el-dialog v-model="showAddCategoryDialog" title="新增分类" width="500px">
      <el-form :model="addCategoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="addCategoryForm.category_name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input v-model="addCategoryForm.description" type="textarea" rows="3" placeholder="请输入分类描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddCategory" :loading="addCategoryLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑分类弹窗 -->
    <el-dialog v-model="showEditCategoryDialog" title="编辑分类" width="500px">
      <el-form :model="editCategoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="editCategoryForm.category_name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input v-model="editCategoryForm.description" type="textarea" rows="3" placeholder="请输入分类描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitEditCategory" :loading="editCategoryLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 知识点详情弹窗 -->
    <el-dialog v-model="showKnowledgeDetailDialog" title="知识点详情" width="600px">
      <div v-if="currentKnowledge">
        <h3 style="margin-bottom: 15px;">{{ currentKnowledge.title }}</h3>
        <p style="color: #666; margin-bottom: 10px;">
          难度：{{ currentKnowledge.difficulty }} | 分类：{{ currentKnowledge.category_name }}
        </p>
        <div class="knowledge-content" v-html="formatContent(currentKnowledge.content)"></div>
      </div>
    </el-dialog>

    <!-- 编辑知识点弹窗 -->
    <el-dialog v-model="showEditKnowledgeDialog" title="编辑知识点" width="600px">
      <el-form :model="editKnowledgeForm" label-width="80px">
        <el-form-item label="知识点标题" required>
          <el-input v-model="editKnowledgeForm.title" placeholder="请输入知识点标题" />
        </el-form-item>
        <el-form-item label="所属分类" required>
          <el-select v-model="editKnowledgeForm.category_id" placeholder="请选择分类">
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.category_name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" required>
          <el-select v-model="editKnowledgeForm.difficulty" placeholder="请选择难度">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="editKnowledgeForm.content" type="textarea" rows="8" placeholder="请输入知识点内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditKnowledgeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitEditKnowledge" :loading="editKnowledgeLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import adminApi from '@/api/admin'

// 标签页
const activeTab = ref('category')

// 🔥 新增：当前选中的分类
const selectedCategory = ref(null)

// ========== 分类管理 ==========
const categoryLoading = ref(false)
const categoryList = ref([])
const showAddCategoryDialog = ref(false)
const showEditCategoryDialog = ref(false)
const addCategoryLoading = ref(false)
const editCategoryLoading = ref(false)
const addCategoryForm = ref({ category_name: '', description: '' })
const editCategoryForm = ref({ id: null, category_name: '', description: '' })

// 加载分类列表
const loadCategoryList = async () => {
  console.log('=== 加载分类列表 ===')
  categoryLoading.value = true
  try {
    const res = await adminApi.getCategoryList()
    categoryList.value = res.data || []
    console.log('分类列表数据:', categoryList.value)
  } catch (error) {
    console.error('获取分类列表失败:', error)
    ElMessage.error('获取分类列表失败')
  } finally {
    categoryLoading.value = false
  }
}

// 🔥 新增：查看分类下的知识点
const viewCategoryKnowledge = (row) => {
  selectedCategory.value = row
  activeTab.value = 'knowledge'
  // 切换到知识点标签页后自动加载该分类的知识点
  loadKnowledgeList(1)
}

// 🔥 新增：清除分类筛选
const clearCategoryFilter = () => {
  selectedCategory.value = null
  loadKnowledgeList(1)
}

// 新增分类
const handleAddCategory = async () => {
  if (!addCategoryForm.value.category_name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  addCategoryLoading.value = true
  try {
    await adminApi.addCategory(addCategoryForm.value)
    ElMessage.success('新增分类成功')
    showAddCategoryDialog.value = false
    addCategoryForm.value = { category_name: '', description: '' }
    loadCategoryList()
  } catch (error) {
    console.error('新增分类失败:', error)
    ElMessage.error('新增分类失败')
  } finally {
    addCategoryLoading.value = false
  }
}

// 编辑分类
const handleEditCategory = (row) => {
  editCategoryForm.value = { ...row }
  showEditCategoryDialog.value = true
}

// 提交编辑分类
const handleSubmitEditCategory = async () => {
  if (!editCategoryForm.value.category_name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  editCategoryLoading.value = true
  try {
    await adminApi.updateCategory(editCategoryForm.value.id, editCategoryForm.value)
    ElMessage.success('编辑分类成功')
    showEditCategoryDialog.value = false
    loadCategoryList()
  } catch (error) {
    console.error('编辑分类失败:', error)
    ElMessage.error('编辑分类失败')
  } finally {
    editCategoryLoading.value = false
  }
}

// 删除分类
const handleDeleteCategory = async (row) => {
  await ElMessageBox.confirm(`确认删除分类「${row.category_name}」？`, '警告', { type: 'warning' })
  try {
    await adminApi.deleteCategory(row.id)
    ElMessage.success('删除成功')
    loadCategoryList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// ========== 知识点管理 ==========
const knowledgeLoading = ref(false)
const knowledgeList = ref([])
const knowledgePage = ref(1)
const knowledgeSize = ref(10)
const knowledgeTotal = ref(0)
const showKnowledgeDetailDialog = ref(false)
const showEditKnowledgeDialog = ref(false)
const editKnowledgeLoading = ref(false)
const currentKnowledge = ref(null)
const editKnowledgeForm = ref({ id: null, title: '', content: '', difficulty: '', category_id: null })

// 🔥 修改：加载知识点列表（支持分类筛选）
const loadKnowledgeList = async (page = 1) => {
  console.log('=== 加载知识点列表 === 页码:', page, '分类ID:', selectedCategory.value?.id)
  knowledgePage.value = page
  knowledgeLoading.value = true
  try {
    // 传递分类ID参数
    const res = await adminApi.getKnowledgeList(page, knowledgeSize.value, selectedCategory.value?.id)
    console.log('知识点接口完整返回:', res)
    knowledgeList.value = res.data?.items || []
    knowledgeTotal.value = res.data?.total || 0
    console.log('知识点列表:', knowledgeList.value)
    console.log('知识点总数:', knowledgeTotal.value)
  } catch (error) {
    console.error('获取知识点列表失败:', error)
    ElMessage.error('获取知识点列表失败')
  } finally {
    knowledgeLoading.value = false
  }
}

// 查看知识点
const handleViewKnowledge = (row) => {
  currentKnowledge.value = row
  showKnowledgeDetailDialog.value = true
}

// 编辑知识点
const handleEditKnowledge = (row) => {
  editKnowledgeForm.value = { ...row }
  showEditKnowledgeDialog.value = true
}

// 提交编辑知识点
const handleSubmitEditKnowledge = async () => {
  if (!editKnowledgeForm.value.title || !editKnowledgeForm.value.content || !editKnowledgeForm.value.category_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  editKnowledgeLoading.value = true
  try {
    await adminApi.updateKnowledge(editKnowledgeForm.value.id, editKnowledgeForm.value)
    ElMessage.success('编辑成功')
    showEditKnowledgeDialog.value = false
    loadKnowledgeList(knowledgePage.value)
  } catch (error) {
    console.error('编辑失败:', error)
    ElMessage.error('编辑失败')
  } finally {
    editKnowledgeLoading.value = false
  }
}

// 删除知识点
const handleDeleteKnowledge = async (row) => {
  await ElMessageBox.confirm(`确认删除知识点「${row.title}」？`, '警告', { type: 'warning' })
  try {
    await adminApi.deleteKnowledge(row.id)
    ElMessage.success('删除成功')
    loadKnowledgeList(knowledgePage.value)
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// ========== 文档管理 ==========
const documentLoading = ref(false)
const documentList = ref([])
const documentPage = ref(1)
const documentSize = ref(10)
const documentTotal = ref(0)
const documentFilter = ref({
  category_id: null,
  audit_status: null,
  is_public: null
})

// 审核状态辅助函数
const getAuditStatusType = (status) => {
  switch (status) {
    case 0: return 'info'
    case 1: return 'success'
    case 2: return 'warning'
    case 3: return 'danger'
    default: return 'info'
  }
}

const getAuditStatusText = (status) => {
  switch (status) {
    case 0: return '未提交'
    case 1: return '已通过'
    case 2: return '待审核'
    case 3: return '已拒绝'
    default: return '未知'
  }
}

// 格式化内容
const formatContent = (content) => {
  return content?.replace(/\n/g, '<br>') || ''
}

// 加载文档列表
const loadDocumentList = async (page = 1) => {
  console.log('=== 加载文档列表 === 页码:', page)
  documentPage.value = page
  documentLoading.value = true
  try {
    const params = {
      page: page,
      page_size: documentSize.value,
      ...documentFilter.value
    }
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    console.log('文档列表请求参数:', params)
    const res = await adminApi.getDocumentList(params)
    console.log('文档接口完整返回:', res)
    documentList.value = res.data?.list || []
    documentTotal.value = res.data?.total || 0
    console.log('文档列表:', documentList.value)
    console.log('文档总数:', documentTotal.value)
  } catch (error) {
    console.error('获取文档列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    documentLoading.value = false
  }
}

// 重置筛选
const resetDocumentFilter = () => {
  documentFilter.value = {
    category_id: null,
    audit_status: null,
    is_public: null
  }
  loadDocumentList()
}

// 🔥 已修复：管理员文档下载（rag_token）
const handleDownloadDocument = async (row) => {
  try {
    let token = localStorage.getItem('rag_token')
    if (!token) {
      ElMessage.error('未获取到管理员Token，请重新登录！')
      return
    }
    token = token.trim().replace(/^Bearer\s+/i, '')
    token = `Bearer ${token}`

    const url = `/api/admin/content/content/document/${row.id}/download`
    const response = await fetch(url, {
      method: 'GET',
      headers: { Authorization: token }
    })

    if (!response.ok) throw new Error('请求失败')
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = row.file_name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
    ElMessage.success('下载成功！')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 删除文档
const handleDeleteDocument = async (row) => {
  await ElMessageBox.confirm(`确认删除文档「${row.title}」？删除后无法恢复！`, '警告', { type: 'error' })
  try {
    await adminApi.deleteDocument(row.id)
    ElMessage.success('删除成功')
    loadDocumentList(documentPage.value)
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// ========== 标签页切换 ==========
const handleTabChange = (name) => {
  console.log('=== 标签页切换 === 新标签页:', name)
  if (name === 'category') {
    loadCategoryList()
    // 切换回分类标签页时清除知识点筛选
    selectedCategory.value = null
  } else if (name === 'knowledge') {
    loadKnowledgeList()
  } else if (name === 'document') {
    loadCategoryList()
    loadDocumentList()
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'knowledge') loadKnowledgeList()
  else if (newTab === 'document') { loadCategoryList(); loadDocumentList() }
})

// 页面加载
onMounted(() => {
  loadCategoryList()
})
</script>

<style scoped>
.content-global { padding: 20px; }
.page-title { margin-bottom: 20px; font-size: 24px; font-weight: 600; color: #303133; }
.knowledge-content { line-height: 1.6; white-space: pre-wrap; }
.filter-bar {
  margin-bottom: 16px;
}
</style>