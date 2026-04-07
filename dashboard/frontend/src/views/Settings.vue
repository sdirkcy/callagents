<template>
  <div class="settings-page">
    <el-card shadow="never">
      <template #header>
        <span>系统设置</span>
      </template>

      <el-empty description="系统设置功能正在开发中...">
        <template #image>
          <el-icon :size="100"><Setting /></el-icon>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue'
</script>

<style scoped>
.settings-page {
  padding: 20px;
}
</style>