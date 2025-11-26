import axios from 'axios'
import { ElMessage } from 'element-plus'

// API服务配置
// 直接从环境变量获取API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/'

// 获取当前环境
const APP_ENV = import.meta.env.VITE_APP_ENV || 'production'

console.log(`当前环境: ${APP_ENV}, API基础URL: ${API_BASE_URL}`)

// 创建axios实例
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
    // 减少控制台噪音的配置
    validateStatus: function (status) {
        // 不抛出错误，让所有状态码都通过，由响应拦截器统一处理
        return status >= 200 && status < 600
    }
})

// 请求拦截器
apiClient.interceptors.request.use(
    (config) => {
        // 从本地存储获取密码并添加到请求头
        const authPassword = localStorage.getItem('authPassword')
        if (authPassword) {
            config.headers['X-Password'] = authPassword
        }
        
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
apiClient.interceptors.response.use(
    (response) => {
        // 检查响应状态码，处理401等错误状态
        if (response.status === 401) {
            localStorage.removeItem('authPassword')
            const errorMessage = response.data.message || '未授权，请重新登录'
            ElMessage.error(errorMessage)
            // 延迟重定向，确保用户能看到错误消息
            setTimeout(() => {
                window.location.href = '/#/login'
            }, 10000)
            // 返回被拒绝的Promise，让调用方进入catch块
            return Promise.reject({ 
                data: { success: false, message: errorMessage },
                response: response 
            })
        }
        
        // 处理其他错误状态码（400-599）
        if (response.status >= 400 && response.status < 600) {
            const errorMessage = response.data?.message || response.data?.detail || '请求失败'
            ElMessage.error(errorMessage)
            // 返回被拒绝的Promise，让调用方进入catch块
            return Promise.reject({ 
                data: { success: false, message: errorMessage },
                response: response 
            })
        }
        
        // 正常响应（200-399）直接返回
        return response
    },
    (error) => {
        // 处理网络错误和配置错误
        if (error.response) {
            const { status, data } = error.response
            const errorMessage = data?.message || data?.detail || '请求失败'
            ElMessage.error(errorMessage)
            // 返回被拒绝的Promise，让调用方进入catch块
            return Promise.reject({ 
                data: { success: false, message: errorMessage },
                response: error.response 
            })
        }
        
        if (error.request) {
            console.error('API请求失败: 网络错误', error.request)
            const errorMessage = '网络连接失败，请检查服务器连接'
            ElMessage.error(errorMessage)
            // 返回被拒绝的Promise，让调用方进入catch块
            return Promise.reject({ 
                data: { success: false, message: errorMessage },
                request: error.request 
            })
        }
        
        console.error('API请求失败: 配置错误', error.message)
        const errorMessage = '请求配置错误，请检查网络设置'
        ElMessage.error(errorMessage)
        // 返回被拒绝的Promise，让调用方进入catch块
        return Promise.reject({ 
            data: { success: false, message: errorMessage },
            message: error.message 
        })
    }
)

// 通知配置API方法
apiClient.getAllNoticeConfigs = () => apiClient.post('/notification-channels/get')

apiClient.createNoticeConfig = (data) => apiClient.post('/notification-channels/add', data)

apiClient.updateNoticeConfig = (data) => apiClient.post('/notification-channels/update', data)

apiClient.deleteNoticeConfig = (id) => apiClient.post('/notification-channels/delete', {channel_id: id})

apiClient.testNoticeConfig = (data) => apiClient.post('/notification-channels/test', data)

// 邮箱配置API方法
apiClient.getAllMailConfigs = () => apiClient.post('/email-configs/get')

apiClient.getNoticeChannels = () => apiClient.post('/notification-channels/get')

apiClient.createMailConfig = (data) => apiClient.post('/email-configs/add', data)

apiClient.updateMailConfig = (data) => apiClient.post('/email-configs/update', data)

apiClient.deleteMailConfig = (account) => apiClient.post('/email-configs/delete', {account: account})

apiClient.testSingleMailConfig = (data) => apiClient.post('/email-configs/test', data)

apiClient.runSchedule = () => apiClient.post('/email-configs/run_schedule')

// 通知服务商API方法
apiClient.getAllNotificationServers = () => apiClient.post('/notification-channels/get_servers')

// 邮箱服务商API方法
apiClient.getAllEmailServers = () => apiClient.post('/email-configs/get_servers')

// 邮件记录API方法
apiClient.getEmailRecords = (params) => apiClient.get('/email-records/', { params })

apiClient.getEmailById = (emailId) => apiClient.get(`/email-records/${emailId}`)

apiClient.createEmailRecord = (data) => apiClient.post('/email-records/', data)

apiClient.updateEmailRecord = (emailId, data) => apiClient.put(`/email-records/${emailId}`, data)

apiClient.deleteEmailRecord = (emailId) => apiClient.delete(`/email-records/${emailId}`)

apiClient.getEmailStatistics = () => apiClient.get('/email-records/statistics/overview')

apiClient.searchEmailRecords = (data) => apiClient.post('/email-records/search', data)

// 移除手动标记邮件状态的功能，发送状态应由系统自动设置

apiClient.getRecentEmails = (hours) => apiClient.get(`/email-records/recent/${hours}`)

apiClient.getEmailsBySentStatus = (sent, limit) => apiClient.get(`/email-records/filter/sent/${sent}`, { params: { limit } })

apiClient.getEmailsByRecipient = (recipient, limit) => apiClient.get(`/email-records/filter/recipient/${encodeURIComponent(recipient)}`, { params: { limit } })

// 新增发送邮件方法
apiClient.sendEmailManual = (emailId) => apiClient.post('/email-records/send-manual', { email_id: emailId })

apiClient.sendEmailsBatch = (emailIds) => apiClient.post('/email-records/send-batch', { email_ids: emailIds })

// 用户API方法

// 认证API方法
apiClient.login = (password) => apiClient.post('/login', { password })

// 导出apiClient供其他组件使用
export { apiClient }