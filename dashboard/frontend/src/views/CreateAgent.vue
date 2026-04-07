<template>
  <div class="create-agent">
    <el-card shadow="never">
      <template #header>
        <span>创建新Agent - 步骤向导</span>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="基础信息" />
        <el-step title="LiveKit连接" />
        <el-step title="模型配置" />
        <el-step title="高级设置" />
        <el-step title="确认创建" />
      </el-steps>

      <div class="step-content">
        <!-- Step 1: 基础信息 -->
        <div v-if="currentStep === 0">
          <h3>步骤1：填写基础信息</h3>
          <el-form :model="formData" label-width="120px">
            <el-form-item label="Agent名称" required>
              <el-input v-model="formData.name" placeholder="请输入Agent名称" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="formData.description"
                type="textarea"
                :rows="3"
                placeholder="请输入Agent描述"
              />
            </el-form-item>
            <el-form-item label="类型">
              <el-radio-group v-model="formData.agent_type">
                <el-radio value="voice">语音对话</el-radio>
                <el-radio value="video">视频对话</el-radio>
                <el-radio value="text">文本聊天</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </div>

        <!-- Step 2: LiveKit连接 -->
        <div v-if="currentStep === 1">
          <h3>步骤2：配置LiveKit连接</h3>
          <p class="step-description">请配置LiveKit服务器连接信息</p>
          <el-form :model="formData" label-width="120px">
            <el-form-item label="LiveKit URL" required>
              <el-input
                v-model="formData.livekit_url"
                placeholder="wss://your-livekit-server.com"
              />
            </el-form-item>
            <el-form-item label="API Key" required>
              <el-input
                v-model="formData.livekit_api_key"
                placeholder="请输入API Key"
              />
            </el-form-item>
            <el-form-item label="API Secret" required>
              <el-input
                v-model="formData.livekit_api_secret"
                type="password"
                placeholder="请输入API Secret"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button @click="testConnection">测试连接</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 其他步骤... -->
        <div v-if="currentStep >= 2">
          <el-empty description="此功能正在开发中..." />
        </div>
      </div>

      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button v-if="currentStep < 4" type="primary" @click="nextStep">
          下一步
        </el-button>
        <el-button v-if="currentStep === 4" type="success" @click="submitForm">
          创建Agent
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const currentStep = ref(0)

const formData = ref({
  name: '',
  description: '',
  agent_type: 'voice',
  livekit_url: '',
  livekit_api_key: '',
  livekit_api_secret: '',
  stt_config: {},
  llm_config: {},
  tts_config: {},
  vad_config: {},
  instructions: '',
  max_tool_steps: 5,
  allow_interruptions: true,
})

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = () => {
  if (currentStep.value < 4) {
    currentStep.value++
  }
}

const testConnection = () => {
  ElMessage.info('连接测试功能开发中...')
}

const submitForm = async () => {
  try {
    // TODO: 提交表单
    ElMessage.success('Agent创建成功！')
    router.push('/agents')
  } catch (error) {
    ElMessage.error('创建失败，请重试')
  }
}
</script>

<style scoped>
.create-agent {
  padding: 20px;
}

.step-content {
  margin: 40px 0;
  min-height: 400px;
}

.step-description {
  color: #909399;
  margin-bottom: 20px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>