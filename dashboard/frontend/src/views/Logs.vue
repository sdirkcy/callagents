<template>
  <div class="logs-page">
    <el-card shadow="never">
      <template #header>
        <span>日志查看</span>
      </template>

      <el-empty description="日志查看功能正在开发中...">
        <template #image>
          <el-icon :size="100"><Document /></el-icon>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.logs-page {
  padding: 20px;
}
</style>