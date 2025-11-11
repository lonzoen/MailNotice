import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'

// 引入Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 引入中文语言包
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const app = createApp(App)

app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')