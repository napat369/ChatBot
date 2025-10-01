<template>
  <div class="app-container">
    <header class="app-header">
      <h1 class="app-title">
        <el-icon class="title-icon"><ChatDotRound /></el-icon>
        深思智聊平台
      </h1>
      <p class="app-subtitle">基于AI的智能对话助手</p>
    </header>
    <main class="app-main">
      <ChatComponent />
    </main>
    <footer class="app-footer">
      <p>&copy; 2024 深思智聊平台 - 让思考更深入，让对话更智能</p>
    </footer>
  </div>
</template>

<script>
import ChatComponent from './components/ChatComponent.vue'
import { ChatDotRound } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    ChatComponent,
    ChatDotRound
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.app-title {
  font-size: 2.5rem;
  font-weight: 300;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 2.5rem;
  color: #ffd700;
}

.app-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  font-weight: 300;
}

.app-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.app-footer {
  text-align: center;
  margin-top: 20px;
  color: white;
  opacity: 0.8;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-container {
    padding: 10px;
  }
  
  .app-title {
    font-size: 2rem;
  }
  
  .title-icon {
    font-size: 2rem;
  }
  
  .app-subtitle {
    font-size: 1rem;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  body {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }
}
</style>