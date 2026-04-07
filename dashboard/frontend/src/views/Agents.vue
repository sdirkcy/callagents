<template>
  <div class="agents-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>Agent列表</span>
          <el-button type="primary" @click="createAgent">
            <el-icon><Plus /></el-icon>
            创建Agent
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <el-row :gutter="20" class="filter-row">
        <el-col :span="8">
          <el-input v-model="searchQuery" placeholder="搜索Agent名称" clearable>
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="statusFilter" placeholder="状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="空闲" value="idle" />
            <el-option label="运行中" value="running" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="loadAgents">刷新</el-button>
        </el-col>
      </el-row>

      <!-- Agent列表 -->
      <el-table
        :data="filteredAgents"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="agent_type" label="类型">
          <template #default="{ row }">
            <el-tag>{{ getAgentTypeLabel(row.agent_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button size="small" @click="viewAgent(row.id)">查看</el-button>
            <el-button size="small" type="primary" @click="editAgent(row.id)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteAgent(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadAgents"
        @current-change="loadAgents"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()

const agents = ref([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const filteredAgents = computed(() => {
  let result = agents.value
  
  if (searchQuery.value) {
    result = result.filter(agent => 
      agent.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(agent => agent.status === statusFilter.value)
  }
  
  return result
})

const getAgentTypeLabel = (type: string) => {
  const labels = {
    voice: '语音对话',
    video: '视频对话',
    text: '文本聊天',
  }
  return labels[type] || type
}

const getStatusLabel = (status: string) => {
  const labels = {
    idle: '空闲',
    running: '运行中',
    error: '错误',
    starting: '启动中',
    stopping: '停止中',
  }
  return labels[status] || status
}

const getStatusType = (status: string) => {
  const types = {
    idle: 'info',
    running: 'success',
    error: 'danger',
    starting: 'warning',
    stopping: 'warning',
  }
  return types[status] || 'info'
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const loadAgents = async () => {
  loading.value = true
  try {
    // TODO: 从API加载数据
    // const response = await api.getAgents()
    // agents.value = response.data
  } catch (error) {
    console.error('加载Agent列表失败:', error)
  } finally {
    loading.value = false
  }
}

const createAgent = () => {
  router.push('/agents/create')
}

const viewAgent = (id: string) => {
  router.push(`/agents/${id}`)
}

const editAgent = (id: string) => {
  router.push(`/agents/${id}/edit`)
}

const deleteAgent = async (id: string) => {
  // TODO: 实现删除功能
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.agents-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-row {
  margin-bottom: 20px;
}
</style>