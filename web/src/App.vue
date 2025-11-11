<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
:root {
  /* 全局主题变量 */
  --primary-color: #2563eb; /* 主色调 - 蓝色 */
  --primary-light: #3b82f6; /* 浅蓝色 */
  --primary-dark: #1d4ed8; /* 深蓝色 */
  --secondary-color: #10b981; /* 次要色 - 绿色 */
  --accent-color: #f59e0b; /* 强调色 - 橙色 */
  --danger-color: #ef4444; /* 危险色 - 红色 */
  
  /* 背景色 */
  --bg-primary: #f8fafc; /* 主背景色 - 非常浅的灰蓝色 */
  --bg-secondary: #f1f5f9; /* 次要背景色 - 浅灰蓝色 */
  --bg-tertiary: #e2e8f0; /* 第三背景色 - 稍深的灰蓝色 */
  
  /* 文本色 */
  --text-primary: #1e293b; /* 主文本色 - 深石板蓝 */
  --text-secondary: #475569; /* 次要文本色 - 中等石板蓝 */
  --text-tertiary: #64748b; /* 第三文本色 - 浅石板蓝 */
  --text-light: #f8fafc; /* 浅色文本 - 用于深色背景 */
  
  /* 边框和分割线 */
  --border-color: #e2e8f0; /* 边框色 */
  --divider-color: #cbd5e1; /* 分割线色 */
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  /* 过渡 */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--text-tertiary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>