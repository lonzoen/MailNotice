import axios from 'axios'
import { ElMessage } from 'element-plus'

// API服务配置
// 直接访问后端服务器地址，后端已配置允许跨域
const API_BASE_URL = 'http://localhost:8080/api'

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
    (response) => response,
    (error) => {
        // 处理401未授权错误
        if (error.response?.status === 401) {
            localStorage.removeItem('authPassword')
            ElMessage.error(error.response.data.message)
            // 返回一个已解决的Promise，避免错误继续向上抛出
            return Promise.resolve({ data: { success: false, message: '未授权，请重新登录' } })
        }
        
        // 处理其他错误
        if (error.response) {
            const { status, data } = error.response
            const errorMessage = data?.message || data?.detail || '请求失败'
            ElMessage.error(errorMessage)
            // 返回一个已解决的Promise，避免错误继续向上抛出
            return Promise.resolve({ data: { success: false, message: errorMessage } })
        }
        
        if (error.request) {
            console.error('API请求失败: 网络错误', error.request)
            ElMessage.error('网络连接失败，请检查服务器连接')
            // 返回一个已解决的Promise，避免错误继续向上抛出
            return Promise.resolve({ data: { success: false, message: '网络连接失败，请检查服务器连接' } })
        }
        
        console.error('API请求失败: 配置错误', error.message)
        ElMessage.error('请求配置错误，请检查网络设置')
        // 返回一个已解决的Promise，避免错误继续向上抛出
        return Promise.resolve({ data: { success: false, message: '请求配置错误，请检查网络设置' } })
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

apiClient.getNoticeChannels = () => apiClient.post('/email-configs/get_notice_channels')

apiClient.createMailConfig = (data) => apiClient.post('/email-configs/add', data)

apiClient.updateMailConfig = (data) => apiClient.post('/email-configs/update', data)

apiClient.deleteMailConfig = (account) => apiClient.post('/email-configs/delete', {account: account})

apiClient.testSingleMailConfig = (data) => apiClient.post('/email-configs/test', data)

apiClient.runSchedule = () => apiClient.post('/email-configs/run_schedule')

// 通知服务商API方法
apiClient.getAllNotificationServers = () => apiClient.post('/notification-channels/get_servers')

// 邮箱服务商API方法
apiClient.getAllEmailServers = () => apiClient.post('/email-configs/get_servers')

// 用户API方法

// 认证API方法
apiClient.login = (password) => apiClient.post('/login', { password })

// 导出apiClient供其他组件使用
export { apiClient }