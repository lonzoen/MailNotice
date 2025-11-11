<template>
  <div class="layout">
    <!-- 未登录时显示登录表单 -->
    <div v-if="!isLoggedIn" class="login-overlay">
      <div class="login-container">
        <el-card class="login-card">

          <div class="login-form">
            <div class="login-input-group">
              <el-input
                  v-model="password"
                  type="password"
                  placeholder="请输入密码"
                  @keyup.enter.prevent="handleLogin"
                  autocomplete="current-password"
                  size="large"
                  class="password-input"
              />
              <el-button
                  type="primary"
                  class="login-button"
                  @click.prevent="handleLogin"
                  :loading="isLoading"
                  size="large"
              >
                登录
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 已登录时显示主界面 -->
    <div v-else>
      <el-container class="main-container">
        <!-- 左侧菜单栏 -->
        <el-aside :width="sidebarWidth" class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
          <el-menu
              :default-active="activeMenu"
              class="menu"
              :collapse="isCollapsed"
              :collapse-transition="false"
              router
          >
            <el-menu-item index="/notice">
              <template #title><span>通知渠道管理</span></template>
            </el-menu-item>
            <el-menu-item index="/mail">
              <template #title><span>邮箱配置管理</span></template>
            </el-menu-item>
            <el-menu-item index="logout" @click="handleLogout">
              <template #title><span>退出登录</span></template>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 右侧内容区 -->
        <el-container>
          <el-main class="content">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component"/>
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </div>
</template>

<script setup>
import {ref, computed, onMounted, onUnmounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'

import {ElMessage} from 'element-plus'
import {apiClient} from '../api.js'

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '200px')
const activeMenu = computed(() => route.path)

// 登录状态管理
const isLoggedIn = ref(false)
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

// 检查登录状态
const checkLoginStatus = () => {
  const savedPassword = localStorage.getItem('authPassword')
  isLoggedIn.value = !!savedPassword

  // 如果已经登录，但当前路径是根路径，则重定向到默认页面
  if (isLoggedIn.value && route.path === '/') {
    router.push('/notice')
  }
}

// 处理登录逻辑
const handleLogin = async (event) => {
  // 阻止表单默认提交行为
  if (event) {
    event.preventDefault()
  }

  if (!password.value.trim()) {
    errorMessage.value = '请输入密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    // 发送请求到后端验证密码
    const response = await apiClient.login(password.value)
    
    // 明确检查登录是否成功
    if (response.data && response.data.success === true) {
      // 验证成功，保存密码到本地存储
      localStorage.setItem('authPassword', password.value)
      isLoggedIn.value = true
      password.value = ''

      ElMessage.success('登录成功')
      
      // 登录成功后跳转到默认页面
      if (route.path === '/' || route.path === '/login') {
        router.push('/notice')
      }
    } else {
      // 登录失败，显示后端返回的错误信息
      const errorMessage = response.data?.message || '登录失败'
      ElMessage.error(errorMessage)
    }
  } catch (error) {
    // 正常情况下不应该进入catch块，因为错误已被拦截器处理
    console.error('意外的错误:', error)
  } finally {
    isLoading.value = false
  }
}

// 处理退出登录
const handleLogout = () => {
  localStorage.removeItem('authPassword')
  isLoggedIn.value = false
  router.replace('/login') // 重置路由
  ElMessage.info('已退出登录')
}

// 响应式处理
const handleResize = () => {
  isCollapsed.value = window.innerWidth < 768
}

onMounted(() => {
  checkLoginStatus()
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.layout {
  height: 100vh;
  background-color: #f0f2f5;
}

.main-container {
  height: 100vh;
}

.login-overlay {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-card {
  width: 500px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background-color: white;
  border-radius: 6px;
}

.card-header {
  text-align: center;
  padding: 20px 0;
  border-bottom: 1px solid #f0f0f0;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 18px;
  font-weight: 500;
}

.login-form {
  padding: 20px;
}

.login-input-group {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.password-input {
  flex: 1;
}

.login-button {
  min-width: 50px;
  padding: 0 20px;
  font-size: 14px;
  background-color: #1890ff;
  border: none;
}

.login-button:hover {
  background-color: #40a9ff;
}

.sidebar {
  display: flex;
  flex-direction: column;
  background: #001529;
  color: #fff;
  transition: all 0.3s;
  position: relative;
  z-index: 10;
  overflow: hidden;
}

/* 菜单项样式 */
.menu {
  flex: 1;
  background: transparent;
  position: relative;
  z-index: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.menu .el-menu-item {
  background: transparent;
  color: rgba(255, 255, 255, 0.65) !important;
  transition: all 0.3s;
  border-radius: 0;
  margin: 0;
  height: 48px;
  line-height: 48px;
}

.menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff !important;
}

.menu .el-menu-item.is-active {
  background: #1890ff !important;
  color: #fff !important;
}

/* 内容区域 */
.content {
  padding: 20px;
  overflow-y: auto;
  background-color: #f0f2f5;
  color: #333;
  position: relative;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }

  .sidebar.sidebar-collapsed {
    transform: translateX(0);
  }

  .content {
    padding: 16px;
  }
  
  .login-card {
    width: 350px;
  }
  
  .login-input-group {
    flex-direction: column;
  }
  
  .login-button {
    width: 100%;
    min-width: auto;
  }
}
</style>