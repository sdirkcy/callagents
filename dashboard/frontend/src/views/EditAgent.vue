<template>
  <div class="edit-agent">
    <el-card shadow="never">
      <template #header>
        <span>编辑Agent</span>
      </template>

      <el-empty description="编辑功能正在开发中...">
        <template #image>
          <el-icon :size="100"><Edit /></el-icon>
        </template>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Edit } from '@element-plus/icons-vue'
</script>

<style scoped>
.edit-agent {
  padding: 20px;
}
</style>