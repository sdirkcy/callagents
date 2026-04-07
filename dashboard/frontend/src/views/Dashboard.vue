<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.totalAgents }}</div>
              <div class="stat-label">总Agent数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.runningAgents }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.errorAgents }}</div>
              <div class="stat-label">错误</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #909399;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.todayLogs }}</div>
              <div class="stat-label">今日日志</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card class="activity-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>最近活动</span>
          <el-button text>查看全部</el-button>
        </div>
      </template>
      
      <el-empty v-if="recentActivities.length === 0" description="暂无活动记录" />
      
      <el-timeline v-else>
        <el-timeline-item
          v-for="activity in recentActivities"
          :key="activity.id"
          :timestamp="activity.timestamp"
          placement="top"
        >
          <el-card>
            <h4>{{ activity.title }}</h4>
            <p>{{ activity.description }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 快速操作 -->
    <el-card class="quick-actions-card" shadow="never">
      <template #header>
        <span>快速操作</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-button type="primary" class="action-button" @click="createAgent">
            <el-icon><Plus /></el-icon>
            创建Agent
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button class="action-button" @click="viewLogs">
            <el-icon><Document /></el-icon>
            查看日志
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button class="action-button" @click="systemSettings">
            <el-icon><Setting /></el-icon>
            系统设置
          </el-button>
        </el-col>
        <el-col :span="6">
          <el-button class="action-button" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, CircleCheck, Warning, Document, Plus, Setting, Refresh } from '@element-plus/icons-vue'

const router = useRouter()

const stats = ref({
  totalAgents: 0,
  runningAgents: 0,
  errorAgents: 0,
  todayLogs: 0,
})

const recentActivities = ref([
  // 示例数据
])

const createAgent = () => {
  router.push('/agents/create')
}

const viewLogs = () => {
  router.push('/logs')
}

const systemSettings = () => {
  router.push('/settings')
}

const refreshData = () => {
  // 刷新数据
  loadStats()
}

const loadStats = async () => {
  // 加载统计数据
  // TODO: 从API获取数据
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-info {
  margin-left: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.activity-card,
.quick-actions-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-button {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.action-button .el-icon {
  margin-bottom: 8px;
  font-size: 24px;
}
</style>