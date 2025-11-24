<template>
  <div class="notice-management">
    <el-card class="header-card">
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <span>通知渠道管理</span>
          <el-button type="primary" @click="showAddDialog = true">新增</el-button>
        </div>
      </template>
      
      <el-table :data="notices" v-loading="loading" empty-text="暂无通知方式数据">

       <el-table-column prop="channelName" label="渠道名称" width="150">
          <template #default="{ row }">
            <span>{{ row.channelName }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="server" label="服务器类型" width="150">
          <template #default="{ row }">
            <span>{{ row.server }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="appKey" label="应用密钥" min-width="200">
          <template #default="{ row }">
            <span class="app-key">{{ maskAppKey(row.appKey) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="success" 
              @click="testNotice(row)"
            >测试</el-button>
            <el-button 
              type="primary" 
              @click="editNotice(row)"
            >编辑</el-button>
            <el-button 
              type="danger" 
              @click="deleteNotice(row.id)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="showEditDialog ? '编辑通知方式' : '新增通知方式'" 
      width="500px"
      :close-on-click-modal="false"
      @close="closeDialog"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="渠道名称" prop="channelName">
          <el-input 
            v-model="formData.channelName" 
            placeholder="请输入渠道名称"
          />
        </el-form-item>
        <el-form-item label="服务器类型" prop="server">
          <el-select v-model="formData.server" placeholder="请选择服务器类型">
            <el-option 
              v-for="server in notificationServers" 
              :key="server.name"
              :label="server.name" 
              :value="server.name" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="应用密钥" prop="appKey">
          <el-input 
            v-model="formData.appKey" 
            placeholder="请输入应用密钥"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeDialog">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ showEditDialog ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { apiClient } from '../api.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const notices = ref([])
const notificationServers = ref([])
const loading = ref(false)
const searchKeyword = ref('')
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const submitting = ref(false)
const formData = reactive({
  id: null,
  server: '',
  channelName: '',
  appKey: ''
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

const formRules = reactive({
  server: [
    { required: true, message: '请选择服务器类型', trigger: 'change' }
  ],
  channelName: [
    { required: true, message: '请输入渠道名称', trigger: 'blur' },
    { min: 1, message: '渠道名称不能为空', trigger: 'blur' }
  ],
  appKey: [
    { required: true, message: '请输入应用密钥', trigger: 'blur' },
    { min: 1, message: '应用密钥不能为空', trigger: 'blur' }
  ]
})

const formRef = ref()

// 掩码显示应用密钥
const maskAppKey = (appKey) => {
  if (!appKey) return ''
  if (appKey.length <= 8) {
    // 如果应用密钥长度小于等于8位，显示前4位，其余用*填充，总长度16位
    const visiblePart = appKey.substring(0, 4)
    const maskedPart = '*'.repeat(16 - visiblePart.length)
    return visiblePart + maskedPart
  } else {
    // 如果应用密钥长度大于8位，显示前4位和后4位，中间用*填充，总长度16位
    const firstPart = appKey.substring(0, 4)
    const lastPart = appKey.substring(appKey.length - 4)
    const middleStars = '*'.repeat(8) // 中间8个*
    return firstPart + middleStars + lastPart
  }
}



// 加载通知服务商列表
const loadNotificationServers = async () => {
  try {
    const response = await apiClient.getAllNotificationServers()
    
    // 检查响应是否包含错误信息（来自API拦截器）
    if (response.data && typeof response.data === 'object' && response.data.success === false) {
      // 如果是错误响应，抛出错误让catch块处理
      throw new Error(response.data.message || '加载通知服务商失败')
    }
    
    notificationServers.value = response.data.map(name => ({ name }))
  } catch (error) {
    console.error('加载通知服务商失败:', error)
    // API拦截器已经显示过错误信息，这里只处理业务逻辑
    // 如果后端不可用，显示空列表
    notificationServers.value = []
  }
}

// 加载通知方式列表
const loadNotices = async () => {
  loading.value = true
  try {
    const response = await apiClient.getAllNoticeConfigs()
    
    // 检查响应是否包含错误信息（来自API拦截器）
    if (response.data && typeof response.data === 'object' && response.data.success === false) {
      // 如果是错误响应，抛出错误让catch块处理
      throw new Error(response.data.message || '加载通知方式失败')
    }
    
    notices.value = response.data.map(item => ({
      id: item.id,
      server: item.server_name || '未设置',
      channelName: item.name || '未设置',
      appKey: item.token || ''
    }))
  } catch (error) {
    console.error('加载通知方式失败:', error)
    // API拦截器已经显示过错误信息，这里只处理业务逻辑
    // 如果后端不可用，显示空列表
    notices.value = []
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 实现搜索逻辑
  console.log('搜索关键词:', searchKeyword.value)
}

// 编辑通知方式
const editNotice = (notice) => {
  Object.assign(formData, notice)
  showEditDialog.value = true
}

// 测试通知方式
const testNotice = async (row) => {
  try {
    // 准备测试数据
    const testData = {
      name: row.channelName,
      token: row.appKey,
      server_name: row.server
    }
    
    // 调用测试API
    const result = await apiClient.testNoticeConfig(testData)
    
    // 检查响应是否包含错误信息（来自API拦截器）
    if (result.data && typeof result.data === 'object' && result.data.success === false) {
      // 如果是错误响应，抛出错误让catch块处理
      throw new Error(result.data.message || '测试通知方式失败')
    }
    
    ElMessage.success('测试发送成功')
  } catch (error) {
    console.error('测试通知方式失败:', error)
    // API拦截器已经显示过错误信息，这里只处理业务逻辑
  }
}

// 删除通知方式
const deleteNotice = async (id) => {
  try {
    await ElMessageBox.confirm('此操作将永久删除该通知方式, 是否继续?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiClient.deleteNoticeConfig(id)
    notices.value = notices.value.filter(notice => notice.id !== id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除通知方式失败:', error)
      // API拦截器已经显示过错误信息，这里只处理业务逻辑
    }
  }
}



// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    if (showEditDialog.value) {
      // 更新通知
      const updateData = {
        channel_id: formData.id,
        name: formData.channelName,
        server_name: formData.server,
        token: formData.appKey
      };
      
      await apiClient.updateNoticeConfig(updateData)
      
      // 更新本地数据
      const index = notices.value.findIndex(n => n.id === formData.id)
      if (index !== -1) {
        notices.value[index] = { 
          ...formData,
          createTime: notices.value[index].createTime
        }
      }
      ElMessage.success('通知更新成功')
    } else {
      // 新增通知
      const newData = {
        name: formData.channelName,
        server_name: formData.server,
        token: formData.appKey
      };
      
      const response = await apiClient.createNoticeConfig(newData);

      // 添加到本地列表
      notices.value.unshift({
        id: response.data.id,
        server: formData.server,
        channelName: formData.channelName,
        appKey: formData.appKey,
        createTime: new Date().toISOString()
      });
      ElMessage.success('通知创建成功');
    }
    closeDialog()
  } catch (error) {
    console.error('保存通知失败:', error)
    // API拦截器已经显示过错误信息，这里只处理业务逻辑
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const closeDialog = () => {
  showAddDialog.value = false
  showEditDialog.value = false
  Object.assign(formData, {
    id: null,
    server: '',
    channelName: '',
    appKey: ''
  })
  
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

onMounted(async () => {
  await loadNotificationServers()
  await loadNotices()
})
</script>

<style scoped>
.notice-management {
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