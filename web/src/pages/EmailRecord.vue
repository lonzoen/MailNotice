<template>
  <div class="email-record-management">
    <el-card class="header-card">
      <template #header>
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
          <span>邮件记录管理</span>
          <!-- 移除所有新增和刷新按钮 -->
        </div>
      </template>

      <!-- 移除搜索表单，改为直接显示邮件记录 -->

      <!-- 移除统计卡片，直接显示邮件记录 -->

      <!-- 移除批量操作工具栏，简化页面 -->
      
      <!-- 邮件记录表格 -->
      <el-table 
        :data="emailRecords" 
        v-loading="loading" 
        empty-text="暂无邮件记录数据"
      >
        <el-table-column prop="sender" label="发件人" min-width="200" />
        <el-table-column prop="recipient" label="收件人" min-width="120" />
        <el-table-column prop="subject" label="邮件主题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="reception_time" label="接收时间" min-width="120">
          <template #default="{ row }">
            {{ formatDateTime(row.reception_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="sent" label="发送状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.sent ? 'success' : 'warning'">
              {{ row.sent ? '已发送' : '未发送' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="success" 
              size="small"
              @click="sendEmail(row.id)"
              :disabled="row.sent"
            >发送</el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteEmail(row.id)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination" style="margin-top: 20px; text-align: right;">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :disabled="loading"
          :background="false"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 移除新增邮件对话框 -->

    <!-- 移除统计对话框 -->
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '../api.js'

const emailRecords = ref([])
const loading = ref(false)

// 分页信息
const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 移除所有新增、编辑、统计、搜索相关功能

// 加载邮件记录列表
const loadEmailRecords = async () => {
  loading.value = true
  try {
    const response = await apiClient.getEmailRecords({
      limit: pagination.size,
      offset: (pagination.current - 1) * pagination.size
    })
    
    if (response.data && Array.isArray(response.data)) {
      emailRecords.value = response.data
      // 如果响应包含总数信息，更新分页
      if (response.headers && response.headers['x-total-count']) {
        pagination.total = parseInt(response.headers['x-total-count'])
      } else {
        // 假设总页数是当前加载的记录数
        pagination.total = response.data.length
      }
    } else {
      emailRecords.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('加载邮件记录失败:', error)
    ElMessage.error('加载邮件记录失败')
    emailRecords.value = []
  } finally {
    loading.value = false
  }
}

// 移除所有搜索和统计相关功能

// 移除编辑邮件功能，邮件内容应由系统自动设置
// const viewEmail = async (email) => {
//   try {
//     await apiClient.markEmailAsSent(email.id)
//     email.sent = true
//     ElMessage.success('邮件已标记为已发送')
//     loadStatistics() // 刷新统计数据
//   } catch (error) {
//     console.error('标记邮件状态失败:', error)
//     ElMessage.error('标记邮件状态失败')
//   }
// }

// 保留删除邮件功能
const deleteEmail = async (emailId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条邮件记录吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiClient.deleteEmailRecord(emailId)
    emailRecords.value = emailRecords.value.filter(email => email.id !== emailId)
    ElMessage.success('删除成功')
    // 移除 loadStatistics() 调用，统计功能已移除
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除邮件失败:', error)
      ElMessage.error('删除邮件失败')
    }
  }
}

// 移除手动标记邮件状态的功能，发送状态应由系统自动设置
// const batchMarkSent = async () => {
//   try {
//     const emailIds = selectedEmails.value.map(email => email.id)
//     const response = await apiClient.batchMarkEmailsSent(emailIds)
    
//     if (response.data) {
//       ElMessage.success(response.data.message || '批量标记成功')
//       // 更新本地数据
//       selectedEmails.value.forEach(email => {
//         const localEmail = emailRecords.value.find(e => e.id === email.id)
//         if (localEmail) {
//           localEmail.sent = true
//         }
//       })
//       selectedEmails.value = []
//       selectAll.value = false
//       loadStatistics() // 刷新统计数据
//     }
//   } catch (error) {
//     console.error('批量标记失败:', error)
//     ElMessage.error('批量标记失败')
//   }
// }

// 保留发送单个邮件功能
const sendEmail = async (emailId) => {
  try {
    const response = await apiClient.sendEmailManual(emailId)
    
    if (response.data) {
      ElMessage.success(response.data.message || '发送成功')
      // 更新本地数据
      const email = emailRecords.value.find(e => e.id === emailId)
      if (email) {
        email.sent = true
      }
      // 移除 loadStatistics() 调用，统计功能已移除
    }
  } catch (error) {
    console.error('发送邮件失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送失败')
  }
}

// 移除批量发送和批量删除功能

// 处理页码变化
const handleCurrentChange = (page) => {
  pagination.current = page
  loadEmailRecords()
}

// 处理每页数量变化
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  loadEmailRecords()
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN')
}

onMounted(async () => {
  await loadEmailRecords()
  // 移除统计数据加载，统计功能已移除
})
</script>

<style scoped>
.email-record-management {
  max-width: 1400px;
  margin: 0 auto;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>