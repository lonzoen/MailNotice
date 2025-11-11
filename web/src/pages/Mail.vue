<template>
  <div class="mail-management">
    <el-card class="header-card">
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <span>邮箱配置管理</span>
          <div style="display: flex; gap: 10px;">
            <el-button 
              type="success" 
              @click="runSchedule"
              :loading="isRunning"
              :icon="Promotion"
            >
              {{ isRunning ? '运行中...' : '立即推送' }}
            </el-button>
            <el-button type="primary" @click="showAddDialog = true">添加配置</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="mailConfigs" v-loading="loading" empty-text="暂无邮箱配置数据">
        <el-table-column prop="account" label="邮箱账号" min-width="100" />
        <el-table-column prop="channel_id" label="渠道名称" min-width="100">
          <template #default="{ row }">
            <span>{{ getChannelLabel(row.channel_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="server_name" label="邮箱类型" min-width="50">
          <template #default="{ row }">
            <span>{{ row.server_name || '未设置' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="授权码" minwidth="150">
          <template #default="{ row }">
            <span class="auth-cell">{{ maskAuth(row.authorization) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="success" 
              @click="testConfig(row)"
            >测试</el-button>
            <el-button 
              type="primary" 
              @click="editConfig(row)"
            >编辑</el-button>
            <el-button 
              type="danger" 
              @click="deleteConfig(row.id)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="showEditDialog ? '编辑邮箱配置' : '新增邮箱配置'" 
      width="500px"
      :close-on-click-modal="false"
      @close="closeDialog"
    >
      <el-form :model="formData" ref="formRef" label-width="80px">
        <el-form-item label="邮箱账号" prop="account">
          <el-input 
            v-model="formData.account" 
            placeholder="请输入邮箱地址"
            type="email"
          />
        </el-form-item>
        <el-form-item label="邮箱类型" prop="server_name">
          <el-select v-model="formData.server_name" placeholder="请选择邮箱类型" style="width: 100%">
            <el-option 
              v-for="server in emailServers" 
              :key="server"
              :label="server" 
              :value="server" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="授权码" prop="authorization">
          <el-input 
            v-model="formData.authorization" 
            placeholder="请输入邮箱授权码"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="渠道名称" prop="channel_id">
          <el-select v-model="formData.channel_id" placeholder="请选择通知渠道" style="width: 100%">
            <el-option 
              v-for="(label, id) in noticeChannels" 
              :key="id"
              :label="label" 
              :value="id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeDialog">取消</el-button>
          <el-button type="primary" @click="submitForm">
            {{ showEditDialog ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {Promotion, VideoPlay} from '@element-plus/icons-vue'
import { apiClient } from '../api.js'

const mailConfigs = ref([])
const emailServers = ref([])
const noticeChannels = ref({})
const loading = ref(false)
const isRunning = ref(false)
const searchKeyword = ref('')
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const submitting = ref(false)
const formData = ref({
    id: null,
    account: '',
    server_name: '',
    authorization: '',
    channel_id: ''
  })

// 计算对话框显示状态
const dialogVisible = computed({
  get: () => showAddDialog.value || showEditDialog.value,
  set: (value) => {
    if (!value) {
      showAddDialog.value = false
      showEditDialog.value = false
    }
  }
})

const formRules = {
  account: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  server_name: [
    { required: true, message: '请选择邮箱类型', trigger: 'blur' }
  ],
  authorization: [
    { required: true, message: '请输入授权码', trigger: 'blur' },
    { min: 6, message: '授权码长度不能少于6位', trigger: 'blur' }
  ]
}

// 加载邮箱服务商列表
const loadEmailServers = async () => {
  try {
    const response = await apiClient.getAllEmailServers()
    emailServers.value = response.data || []
  } catch (error) {
    console.error('加载邮箱服务商失败:', error)
    // 显示后端返回的具体错误信息
    const errorMessage = error.message || error.data?.message || '加载邮箱服务商失败'
    ElMessage.error(errorMessage)
    emailServers.value = []
  }
}

// 加载通知渠道
const loadNoticeChannels = async () => {
  try {
    const response = await apiClient.getNoticeChannels()
    // 将API返回的格式转换为 {channel_id: label} 的映射对象
    const channelsMap = {}
    response.data.forEach(item => {
      const [channelId, label] = Object.entries(item)[0]
      channelsMap[channelId] = label
    })
    noticeChannels.value = channelsMap
  } catch (error) {
    console.error('加载通知渠道失败:', error)
    noticeChannels.value = {}
  }
}

// 加载邮箱配置列表
const loadMailConfigs = async () => {
  loading.value = true
  try {
    const response = await apiClient.getAllMailConfigs()
    mailConfigs.value = response.data.map(item => ({
      id: item.account, // 使用account作为唯一标识
      account: item.account || '未设置',
      server_name: item.server_name || '未设置',
      authorization: item.auth_code || '',
      channel_id: item.channel_id || ''
    }))
  } catch (error) {
    console.error('加载邮箱配置失败:', error)
    // 显示后端返回的具体错误信息
    const errorMessage = error.message || error.data?.message || '加载邮箱配置失败'
    ElMessage.error(errorMessage)
    // 如果后端不可用，显示空列表
    mailConfigs.value = []
  } finally {
    loading.value = false
  }
}

// 运行定时任务
const runSchedule = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  try {
    const response = await apiClient.runSchedule()
    
    // 根据后端返回格式处理响应
    if (response.data.success) {
      ElMessage.success({
        message: response.data.message || '任务执行成功！',
        duration: 5000
      })
    } else {
      throw new Error(response.data.message || '任务执行失败')
    }
  } catch (error) {
    console.error('执行定时任务失败:', error)
    const errorMessage = error.message || error.data?.message || '任务执行失败，请检查网络连接或后端服务'
    ElMessage.error(errorMessage)
  } finally {
    isRunning.value = false
  }
}

// 掩码显示授权码
const maskAuth = (auth) => {
  if (!auth) return ''
  if (auth.length <= 8) {
    // 如果授权码长度小于等于8位，显示前4位，其余用*填充，总长度16位
    const visiblePart = auth.substring(0, 4)
    const maskedPart = '*'.repeat(16 - visiblePart.length)
    return visiblePart + maskedPart
  } else {
    // 如果授权码长度大于8位，显示前4位和后4位，中间用*填充，总长度16位
    const firstPart = auth.substring(0, 4)
    const lastPart = auth.substring(auth.length - 4)
    const middleStars = '*'.repeat(8) // 中间8个*
    return firstPart + middleStars + lastPart
  }
}

// 测试配置
const testConfig = async (config) => {
  try {
    loading.value = true
    
    // 构建测试配置对象
    const testData = {
      account: config.account,
      auth_code: config.authorization,
      server_name: config.server_name,
      channel_id: config.channel_id
    }
    
    const response = await apiClient.testSingleMailConfig(testData)
    
    if (response.data.success) {
      ElMessage.success(`测试成功: ${response.data.message || '配置正常'}`)
    } else {
      ElMessage.error(`测试失败: ${response.data.message || '配置异常'}`)
    }
  } catch (error) {
    console.error('测试配置失败:', error)
    const errorMessage = error.message || error.data?.message || '测试失败，请检查配置'
    ElMessage.error(`测试失败: ${errorMessage}`)
  } finally {
    loading.value = false
  }
}

// 编辑配置
const editConfig = (config) => {
  formData.value = { ...config }
  showEditDialog.value = true
}

// 删除配置
const deleteConfig = async (account) => {
  try {
    await ElMessageBox.confirm('确定要删除这个邮箱配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await mailConfigAPI.delete(account)
    mailConfigs.value = mailConfigs.value.filter(config => config.account !== account)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      // 显示后端返回的具体错误信息
      const errorMessage = error.message || error.data?.message || '删除失败，请重试'
      ElMessage.error(errorMessage)
    }
  }
}

// 提交表单
const submitForm = async () => {
  try {
    submitting.value = true
    
    if (showEditDialog.value) {
      // 编辑配置，直接调用update API
      const response = await mailConfigAPI.update({
        account: formData.value.account,
        auth_code: formData.value.authorization,
        server: '', // 服务器信息需要从服务商获取
        server_name: formData.value.server_name,
        channel_id: formData.value.channel_id || 1 // 使用表单中选择的渠道ID，如果未选择则使用默认值1
      })
      
      // 更新本地数据
      const index = mailConfigs.value.findIndex(c => c.account === formData.value.account)
      if (index !== -1) {
        mailConfigs.value[index] = { 
          ...formData.value,
          id: formData.value.account // 使用account作为唯一标识
        }
      }
      ElMessage.success('邮箱配置更新成功')
    } else {
      // 新增配置，直接调用create API
      const response = await mailConfigAPI.create({
        account: formData.value.account,
        auth_code: formData.value.authorization,
        server: '', // 服务器信息需要从服务商获取
        server_name: formData.value.server_name,
        channel_id: formData.value.channel_id || 1 // 使用表单中选择的渠道ID，如果未选择则使用默认值1
      })
      
      // 添加到本地列表
      mailConfigs.value.unshift({
        ...formData.value,
        id: formData.value.account, // 使用account作为唯一标识
        createTime: new Date().toISOString()
      })
      ElMessage.success('邮箱配置创建成功')
    }
    closeDialog()
  } catch (error) {
    console.error('保存邮箱配置失败:', error)
    // 显示后端返回的具体错误信息
    const errorMessage = error.message || error.data?.message || '操作失败，请重试'
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
  const closeDialog = () => {
    // 保留当前模式状态，避免按钮文本变化
    const wasEditMode = showEditDialog.value
    showAddDialog.value = false
    showEditDialog.value = false
    formData.value = {
      id: null,
      account: '',
      server_name: '',
      authorization: '',
      channel_id: ''
    }
  }

// 格式化日期
// 获取渠道标签
const getChannelLabel = (channelId) => {
  if (!channelId || !noticeChannels.value[channelId]) {
    return '未设置'
  }
  return noticeChannels.value[channelId]
}

onMounted(async () => {
  await loadEmailServers()
  await loadNoticeChannels()
  await loadMailConfigs()
})
</script>

<style scoped>
.mail-management {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #2c3e50;
}

.search-area {
  margin-bottom: 20px;
}

.search-input {
  position: relative;
  max-width: 300px;
}

.search-input input {
  width: 100%;
  padding: 8px 35px 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}



.actions {
  display: flex;
  gap: 8px;
}




</style>