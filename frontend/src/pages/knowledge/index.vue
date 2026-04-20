<template>
  <div class='knowledge-page'>
    <el-card>
      <template #header>
        <div class='card-header'>
          <span>知识库管理</span>
          <el-button type='primary'>新建知识库</el-button>
        </div>
      </template>
      <el-empty description='暂无知识库，点击右上角按钮新建第一个知识库吧' />
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped lang='scss'>
.knowledge-page {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
