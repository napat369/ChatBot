<template>
  <div class="chat-container">
    <!-- 聊天历史区域 -->
    <div class="chat-history" ref="chatHistoryRef" @scroll="handleScroll">
      <div v-if="chatHistory.length === 0" class="empty-state">
        <el-empty description="暂无聊天记录，开始您的第一次对话吧！" />
      </div>
      <div v-for="(item, index) in chatHistory" :key="index" class="chat-item">
        <!-- 时间分隔线 -->
        <div v-if="shouldShowTimeDivider(index)" class="time-divider">
          <span>{{ formatTime(item.create_time) }}</span>
        </div>
        
        <div class="user-question">
          <div class="question-content">
            <div class="message-text">{{ item.question }}</div>
            <div class="message-time">{{ formatMessageTime(item.create_time) }}</div>
          </div>
          <el-avatar icon="UserFilled" class="user-avatar"></el-avatar>
        </div>
        
        <div class="ai-answer" v-if="item.answer || item.user_type === 'assistant'">
          <el-avatar icon="Service" class="ai-avatar"></el-avatar>
          <div class="answer-content">
            <div class="message-text">
              <span v-html="formatAnswer(item.answer || '')"></span>
              <span v-if="item.isStreaming" class="typing-cursor">|</span>
            </div>
            <div class="message-time" v-if="!item.isStreaming">{{ formatMessageTime(item.create_time) }}</div>
            <div class="streaming-indicator" v-if="item.isStreaming">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在生成回答...</span>
            </div>
            <!-- 停止生成标识 -->
            <div v-if="item.isStopped" class="stopped-indicator">
              <el-icon><Close /></el-icon>
              <span>手动停止生成</span>
            </div>
          </div>
        </div>
        
        <div class="ai-answer" v-else-if="item.id === currentQuestionId && loading">
          <el-avatar icon="Service" class="ai-avatar"></el-avatar>
          <div class="answer-content loading-content">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>AI正在思考中，结合您的对话历史...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 回到底部按钮 -->
    <div v-if="userScrolled && !isNearBottom" class="back-to-bottom" @click="forceScrollToBottom">
      <el-button type="primary" size="small" circle>
        <el-icon><ArrowDown /></el-icon>
      </el-button>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input">
      <el-input
        v-model="userQuestion"
        type="textarea"
        :rows="2"
        placeholder="请输入您的问题（按Enter发送，Shift+Enter换行）"
        :disabled="loading"
        @keydown="handleKeyDown"
        maxlength="5000"
        show-word-limit
        resize="none"
      ></el-input>
      <div class="input-actions">
        <el-button 
          type="primary" 
          @click="sendQuestion" 
          :loading="loading"
          :disabled="!userQuestion.trim()"
        >
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
        <el-button 
          type="danger" 
          @click="stopGeneration" 
          :disabled="!isStreaming"
          class="stop-btn"
        >
          <el-icon><Close /></el-icon>
          停止生成
        </el-button>
        <el-button 
          type="success" 
          @click="newConversation" 
          :disabled="loading"
        >
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
        <el-button 
          type="info" 
          @click="showSessionHistory" 
          :disabled="loading"
        >
          <el-icon><Clock /></el-icon>
          历史记录
        </el-button>
        <el-button @click="clearHistory" :disabled="loading || chatHistory.length === 0">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>
  </div>

  <!-- 会话历史对话框 -->
  <el-dialog
    v-model="sessionHistoryVisible"
    title="历史会话"
    width="90%"
    :before-close="handleCloseSessionHistory"
    class="session-history-dialog"
  >
    <div class="session-history-container">
      <!-- 会话列表 -->
      <div class="session-list" v-show="!selectedSession">
        <div class="session-list-header">
          <h3>会话列表</h3>
          <el-button 
            type="text" 
            @click="fetchSessions"
            :loading="sessionsLoading"
            size="small"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <div v-if="sessionsLoading" class="loading-container">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div v-else-if="sessions.length === 0" class="empty-sessions">
          <el-empty description="暂无历史会话" />
        </div>
        <div v-else class="sessions-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            class="session-item"
            @click="selectSession(session)"
          >
            <div class="session-content">
              <div class="session-title">{{ session.title }}</div>
              <div class="session-info">
                <span class="question-count">{{ session.question_count }} 条对话</span>
                <span class="update-time">{{ formatSessionTime(session.update_time) }}</span>
              </div>
            </div>
            <div class="session-actions">
              <el-button 
                type="text" 
                size="small"
                @click.stop="deleteSession(session)"
                class="delete-btn"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 会话详情 -->
      <div class="session-detail" v-show="selectedSession">
        <div class="session-detail-header">
          <el-button 
            type="text" 
            @click="backToSessionList"
            size="small"
            class="back-btn"
          >
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
          <h3>{{ selectedSession?.title }}</h3>
          <div class="session-detail-actions">
            <el-button 
              type="primary" 
              size="small"
              @click="continueSession"
            >
              继续对话
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteCurrentSession"
            >
              删除会话
            </el-button>
          </div>
        </div>
        
        <div class="session-detail-content">
          <div v-if="sessionDetailLoading" class="loading-container">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载对话历史中...</span>
          </div>
          <div v-else-if="sessionMessages.length === 0" class="empty-messages">
            <el-empty description="此会话暂无对话记录" />
          </div>
          <div v-else class="session-messages">
            <div 
              v-for="message in sessionMessages" 
              :key="message.id"
              class="message-item"
            >
              <div class="user-message">
                <div class="message-header">
                  <strong>用户</strong>
                  <span class="message-time">{{ formatMessageTime(message.create_time) }}</span>
                </div>
                <div class="message-content">{{ message.question }}</div>
              </div>
              <div v-if="message.answer" class="bot-message">
                <div class="message-header">
                  <strong>助手</strong>
                </div>
                <div class="message-content" v-html="formatAnswer(message.answer)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Promotion, Delete, Loading, Plus, Refresh, ArrowLeft, Close, ArrowDown } from '@element-plus/icons-vue';
import axios from 'axios';

// 配置axios
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.timeout = 60000; // 增加到60秒，适应AI回答生成时间

// 请求拦截器
axios.interceptors.request.use(
  config => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
axios.interceptors.response.use(
  response => {
    console.log('收到响应:', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('响应错误:', error);
    if (error.response) {
      const { status, data } = error.response;
      let message = '请求失败';
      
      switch (status) {
        case 400:
          message = data.message || '请求参数错误';
          break;
        case 500:
          message = data.message || '服务器内部错误';
          break;
        case 503:
          message = '服务暂时不可用';
          break;
        default:
          message = data.message || `请求失败 (${status})`;
      }
      
      ElMessage.error(message);
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试');
    } else {
      ElMessage.error('网络连接失败');
    }
    return Promise.reject(error);
  }
);

export default {
  name: 'ChatComponent',
  components: {
    Promotion,
    Delete,
    Loading,
    Plus,
    Refresh,
    ArrowLeft,
    Close
  },
  setup() {
    const userQuestion = ref('');
    const chatHistory = ref([]);
    const loading = ref(false);
    const currentQuestionId = ref(null);
    const chatHistoryRef = ref(null);
    const userId = 1; // 假设用户ID为1
    
    // 会话管理相关数据
    const sessionHistoryVisible = ref(false);
    const sessions = ref([]);
    const sessionsLoading = ref(false);
    const selectedSession = ref(null);
    const sessionMessages = ref([]);
    const sessionDetailLoading = ref(false);
    const currentSessionId = ref(null);
    
    // 停止生成相关状态
    const isStreaming = ref(false);
    const currentEventSource = ref(null); // 保存EventSource引用
    
    // 添加用户滚动状态检测
    const userScrolled = ref(false); // 用户是否手动滚动
    const isNearBottom = ref(true); // 是否接近底部
    
    // 检测用户是否手动滚动
    const handleScroll = () => {
      if (chatHistoryRef.value) {
        const { scrollTop, scrollHeight, clientHeight } = chatHistoryRef.value;
        const threshold = 100; // 距离底部100px内认为是在底部
        
        isNearBottom.value = scrollHeight - scrollTop - clientHeight <= threshold;
        
        // 如果用户滚动到了非底部位置，标记为手动滚动
        if (!isNearBottom.value) {
          userScrolled.value = true;
        } else if (isNearBottom.value && userScrolled.value) {
          // 如果用户滚动回到底部，重置手动滚动状态
          userScrolled.value = false;
        }
      }
    };
    
    // 格式化答案显示
    const formatAnswer = (answer) => {
      if (!answer) return '';
      return answer
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
    };
    
    // 格式化时间显示
    const formatTime = (timeString) => {
      const date = new Date(timeString);
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      
      if (messageDate.getTime() === today.getTime()) {
        return '今天';
      } else if (messageDate.getTime() === today.getTime() - 24 * 60 * 60 * 1000) {
        return '昨天';
      } else {
        return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' });
      }
    };
    
    // 格式化消息时间
    const formatMessageTime = (timeString) => {
      const date = new Date(timeString);
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
    };
    
    // 判断是否显示时间分隔线
    const shouldShowTimeDivider = (index) => {
      if (index === 0) return true;
      
      const currentDate = new Date(chatHistory.value[index].create_time);
      const prevDate = new Date(chatHistory.value[index - 1].create_time);
      
      // 如果日期不同，显示分隔线
      return currentDate.toDateString() !== prevDate.toDateString();
    };
    
    // 滚动到底部 - 修改为只在用户未手动滚动时才自动滚动
    const scrollToBottom = () => {
      nextTick(() => {
        if (chatHistoryRef.value && !userScrolled.value) {
          chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
        }
      });
    };
    
    // 强制滚动到底部（用于回到底部按钮）
    const forceScrollToBottom = () => {
      nextTick(() => {
        if (chatHistoryRef.value) {
          chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
          userScrolled.value = false; // 重置手动滚动状态
        }
      });
    };
    
    // 处理键盘事件
    const handleKeyDown = (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
      }
    };
    
    // 发送问题
    const sendQuestion = async () => {
      const question = userQuestion.value.trim();
      if (!question || loading.value) return;
      
      loading.value = true;
      isStreaming.value = true; // 设置流式传输状态
      currentQuestionId.value = null;
      
      // 立即显示用户问题
      const userMessage = {
        id: Date.now(), // 临时ID
        question: question,
        answer: null,
        create_time: new Date().toISOString(),
        user_type: 'user'
      };
      
      chatHistory.value.push(userMessage);
      const originalQuestion = userQuestion.value;
      userQuestion.value = '';
      scrollToBottom();
      
      // 添加AI回答占位符
      const aiMessage = {
        id: Date.now() + 1, // 临时ID
        question: null,
        answer: '',
        create_time: new Date().toISOString(),
        user_type: 'assistant',
        isStreaming: true
      };
      
      chatHistory.value.push(aiMessage);
      const aiMessageIndex = chatHistory.value.length - 1;
      scrollToBottom();
      
      try {
        // 构建流式请求参数
        const params = new URLSearchParams({
          user_id: userId,
          question: originalQuestion
        });
        
        // 如果有当前会话ID，添加到请求中
        if (currentSessionId.value) {
          params.append('session_id', currentSessionId.value);
        }
        
        // 使用EventSource接收流式数据
        const eventSource = new EventSource(`http://localhost:8000/api/questions/stream?${params.toString()}`);
        currentEventSource.value = eventSource; // 保存EventSource引用
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'question') {
              // 问题已保存，更新ID和会话ID
              currentQuestionId.value = data.data.id;
              userMessage.id = data.data.id;
              if (data.data.session_id) {
                currentSessionId.value = data.data.session_id;
              }
            } else if (data.type === 'chunk') {
              // 接收AI回答内容片段
              chatHistory.value[aiMessageIndex].answer += data.data.chunk;
              scrollToBottom();
            } else if (data.type === 'complete') {
              // AI回答完成
              chatHistory.value[aiMessageIndex].isStreaming = false;
              chatHistory.value[aiMessageIndex].id = data.data.question_id;
              eventSource.close();
              currentEventSource.value = null; // 清空EventSource引用
              isStreaming.value = false; // 重置流式传输状态
              loading.value = false;
              ElMessage.success('回答完成');
            } else if (data.type === 'error') {
              // 处理错误
              throw new Error(data.message || '生成回答时发生错误');
            }
          } catch (parseError) {
            console.error('解析流式数据失败:', parseError);
            eventSource.close();
            currentEventSource.value = null; // 清空EventSource引用
            isStreaming.value = false; // 重置流式传输状态
            throw parseError;
          }
        };
        
        eventSource.onerror = (error) => {
           console.error('EventSource连接错误:', error);
           eventSource.close();
           
           // 移除失败的消息
           chatHistory.value.pop(); // 移除AI占位符
           chatHistory.value.pop(); // 移除用户消息
           userQuestion.value = originalQuestion; // 恢复用户输入
           
           // 提供用户反馈
           ElMessage.error('连接失败，请检查网络后重试');
           loading.value = false;
           currentQuestionId.value = null;
         };
         
      } catch (error) {
        console.error('发送问题失败', error);
        
        // 移除失败的消息
        chatHistory.value.pop(); // 移除AI占位符
        chatHistory.value.pop(); // 移除用户消息
        userQuestion.value = originalQuestion; // 恢复用户输入
        
        // 根据错误类型提供不同的用户反馈
        ElMessage.error('发送失败，请检查网络连接后重试');
        loading.value = false;
        isStreaming.value = false; // 重置流式传输状态
        currentEventSource.value = null; // 清空EventSource引用
        currentQuestionId.value = null;
      }
    };
    
    // 停止生成功能
    const stopGeneration = () => {
      if (currentEventSource.value && isStreaming.value) {
        // 关闭EventSource连接
        currentEventSource.value.close();
        currentEventSource.value = null;
        
        // 更新状态
        isStreaming.value = false;
        loading.value = false;
        
        // 停止当前消息的流式显示
        const lastMessage = chatHistory.value[chatHistory.value.length - 1];
        if (lastMessage && lastMessage.isStreaming) {
          lastMessage.isStreaming = false;
          // 添加停止标识字段
          lastMessage.isStopped = true;
          // 添加停止标识文本
          if (lastMessage.answer) {
            lastMessage.answer += '\n\n[生成已停止]';
          } else {
            lastMessage.answer = '[生成已停止]';
          }
        }
        
        ElMessage.warning('生成已停止');
      }
    };
    
    // 清空历史记录（删除数据库数据）
    const clearHistory = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有聊天记录吗？此操作将永久删除数据库中的历史数据，不可恢复。',
          '确认清空',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );
        
        // 调用后端API删除数据库中的历史记录
        try {
          const response = await axios.delete(`/api/history/${userId}`);
          chatHistory.value = [];
          ElMessage.success(`聊天记录已清空，删除了 ${response.data.deleted_count} 条数据`);
        } catch (error) {
          console.error('清空历史记录失败', error);
          if (error.response) {
            const status = error.response.status;
            if (status === 404) {
              ElMessage.info('没有历史记录需要清空');
            } else if (status === 500) {
              ElMessage.error('服务器错误，清空失败');
            } else {
              ElMessage.error(`清空失败 (${status})`);
            }
          } else {
            ElMessage.error('网络错误，清空失败');
          }
        }
      } catch {
        // 用户取消操作
      }
    };

    // 创建新对话
    const newConversation = () => {
      // 清空当前显示的对话历史，但不删除数据库数据
      chatHistory.value = [];
      userQuestion.value = '';
      currentQuestionId.value = null;
      currentSessionId.value = null; // 重置会话ID
      ElMessage.success('已开始新对话');
    };
    
    // 显示会话历史对话框
    const showSessionHistory = async () => {
      sessionHistoryVisible.value = true;
      await fetchSessions();
    };
    
    // 获取会话列表
    const fetchSessions = async () => {
      sessionsLoading.value = true;
      try {
        const response = await axios.get(`/api/sessions/${userId}`);
        sessions.value = response.data;
      } catch (error) {
        console.error('获取会话列表失败', error);
        ElMessage.error('获取会话列表失败');
      } finally {
        sessionsLoading.value = false;
      }
    };
    
    // 选择会话
    const selectSession = async (session) => {
      selectedSession.value = session;
      sessionDetailLoading.value = true;
      
      try {
        const response = await axios.get(`/api/sessions/${session.id}/history?user_id=${userId}`);
        sessionMessages.value = response.data;
      } catch (error) {
        console.error('获取会话历史失败', error);
        ElMessage.error('获取会话历史失败');
      } finally {
        sessionDetailLoading.value = false;
      }
    };
    
    // 继续会话
    const continueSession = () => {
      if (!selectedSession.value) return;
      
      const sessionTitle = selectedSession.value.title; // 保存标题
      
      // 设置当前会话ID
      currentSessionId.value = selectedSession.value.id;
      // 加载会话历史到当前聊天界面
      chatHistory.value = [...sessionMessages.value];
      // 关闭对话框
      sessionHistoryVisible.value = false;
      // 清空选择状态
      selectedSession.value = null;
      sessionMessages.value = [];
      
      ElMessage.success(`已切换到会话：${sessionTitle}`);
      scrollToBottom();
    };
    
    // 删除会话
    const deleteSession = async (session) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除会话"${session.title}"吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        );
        
        await axios.delete(`/api/sessions/${session.id}?user_id=${userId}`);
        ElMessage.success('会话已删除');
        
        // 刷新会话列表
        await fetchSessions();
        
        // 如果删除的是当前选中的会话，清空选择状态
        if (selectedSession.value && selectedSession.value.id === session.id) {
          selectedSession.value = null;
          sessionMessages.value = [];
        }
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除会话失败', error);
          ElMessage.error('删除会话失败');
        }
      }
    };
    
    // 删除当前会话
    const deleteCurrentSession = async () => {
      if (!selectedSession.value) return;
      await deleteSession(selectedSession.value);
      // 删除后返回会话列表
      selectedSession.value = null;
      sessionMessages.value = [];
    };
    
    // 返回会话列表
    const backToSessionList = () => {
      selectedSession.value = null;
      sessionMessages.value = [];
    };
    
    // 关闭会话历史对话框
    const handleCloseSessionHistory = () => {
      sessionHistoryVisible.value = false;
      selectedSession.value = null;
      sessionMessages.value = [];
    };
    
    // 格式化时间显示（用于会话列表）
    const formatSessionTime = (timeString) => {
      const date = new Date(timeString);
      const now = new Date();
      const diffTime = now - date;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return date.toLocaleTimeString('zh-CN', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        });
      } else if (diffDays === 1) {
        return '昨天';
      } else if (diffDays < 7) {
        return `${diffDays}天前`;
      } else {
        return date.toLocaleDateString('zh-CN', { 
          month: 'short', 
          day: 'numeric' 
        });
      }
    };
    
    // 页面加载时不自动获取历史记录，默认开始新对话
    onMounted(() => {
      // 不调用fetchHistory，每次打开页面都是新对话
      ElMessage.info('欢迎使用深思智聊平台，已为您开始新对话');
    });
    
    return {
      userQuestion,
      chatHistory,
      loading,
      currentQuestionId,
      chatHistoryRef,
      formatAnswer,
      formatTime,
      formatMessageTime,
      shouldShowTimeDivider,
      handleKeyDown,
      sendQuestion,
      stopGeneration,
      clearHistory,
      newConversation,
      // 停止生成相关状态
      isStreaming,
      currentEventSource,
      // 滚动相关状态和函数
      userScrolled,
      isNearBottom,
      handleScroll,
      forceScrollToBottom,
      // 会话管理相关
      sessionHistoryVisible,
      sessions,
      sessionsLoading,
      selectedSession,
      sessionMessages,
      sessionDetailLoading,
      showSessionHistory,
      selectSession,
      continueSession,
      deleteSession,
      deleteCurrentSession,
      backToSessionList,
      handleCloseSessionHistory,
      formatSessionTime
    };
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 75vh;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  scroll-behavior: smooth;
}

.chat-history::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-history::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-history::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}

.chat-item {
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-question, .ai-answer {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
}

.user-question {
  justify-content: flex-end;
}

.ai-answer {
  justify-content: flex-start;
}

.question-content, .answer-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  word-break: break-word;
  line-height: 1.5;
  position: relative;
}

.message-text {
  margin-bottom: 4px;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  text-align: right;
  margin-top: 4px;
}

.question-content .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.answer-content .message-time {
  color: #909399;
}

.time-divider {
  text-align: center;
  margin: 16px 0;
  position: relative;
}

.time-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e4e7ed;
  z-index: 1;
}

.time-divider span {
  background: #f5f7fa;
  padding: 4px 12px;
  font-size: 12px;
  color: #909399;
  border-radius: 12px;
  position: relative;
  z-index: 2;
}

.question-content {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  margin-right: 12px;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.answer-content {
  background: #ffffff;
  margin-left: 12px;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  color: #303133;
}

.loading-content {
  display: flex;
  align-items: center;
  color: #909399;
  font-style: italic;
}

.loading-content .el-icon {
  margin-right: 8px;
}

.chat-input {
  padding: 16px;
  background: #ffffff;
  border-top: 1px solid #e4e7ed;
}

.chat-input .el-textarea {
  margin-bottom: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-actions .el-button {
  min-width: 80px;
}

.user-avatar, .ai-avatar {
  align-self: flex-start;
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.ai-avatar {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

/* 会话历史对话框样式 */
.session-history-container {
  height: 60vh;
  display: flex;
  flex-direction: column;
}

.session-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.session-list-header h3 {
  margin: 0;
  color: #303133;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #909399;
}

.loading-container .el-icon {
  margin-right: 8px;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.session-item:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
}

.session-content {
  flex: 1;
}

.session-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.session-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.session-actions {
  margin-left: 12px;
}

.delete-btn {
  color: #f56c6c;
}

.delete-btn:hover {
  color: #f56c6c;
  background-color: #fef0f0;
}

.session-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.session-detail-header h3 {
  margin: 0;
  color: #303133;
  flex: 1;
  text-align: center;
}

.back-btn {
  color: #409eff;
}

.session-detail-actions {
  display: flex;
  gap: 8px;
}

.session-detail-content {
  flex: 1;
  overflow-y: auto;
}

.session-messages {
  padding: 16px 0;
}

.message-item {
  margin-bottom: 16px;
}

.user-message, .bot-message {
  margin-bottom: 8px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
}

.message-header strong {
  color: #303133;
}

.message-content {
  padding: 8px 12px;
  border-radius: 8px;
  line-height: 1.5;
}

.user-message .message-content {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.bot-message .message-content {
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
}

/* 流式显示效果 */
.typing-cursor {
  animation: blink 1s infinite;
  color: #409eff;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.streaming-indicator .el-icon {
  font-size: 14px;
}

/* 停止生成按钮动画效果 */
.stop-btn:not(:disabled) .el-icon {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.stop-btn:not(:disabled) {
  background: linear-gradient(135deg, #f56c6c 0%, #ff7875 100%);
  border-color: #f56c6c;
  color: white;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.3);
}

.stop-btn:not(:disabled):hover {
  background: linear-gradient(135deg, #f78989 0%, #ff9c9c 100%);
  border-color: #f78989;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
  transform: translateY(-1px);
}

.stop-btn:disabled {
  background: #f5f7fa;
  border-color: #e4e7ed;
  color: #c0c4cc;
  cursor: not-allowed;
  box-shadow: none;
}

/* 停止生成标识样式 */
.stopped-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
  padding: 4px 8px;
  background-color: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 4px;
  width: fit-content;
}

.stopped-indicator .el-icon {
  font-size: 14px;
}

/* 停止生成按钮动画效果 */
.stop-btn:not(:disabled) .el-icon {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* 回到底部按钮样式 */
.back-to-bottom {
  position: absolute;
  bottom: 120px;
  right: 20px;
  z-index: 1000;
  animation: fadeInUp 0.3s ease-out;
}

.back-to-bottom .el-button {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  border: none;
}

.back-to-bottom .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>