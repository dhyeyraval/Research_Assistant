import axios from 'axios';

// Connect to your FastAPI local development server
const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authAPI = {
  loginOrCreate: async (username) => {
    const response = await api.post('/auth/login', { username });
    return response.data;
  },
};

export const chatsAPI = {
  getUserChats: async (userId) => {
    const response = await api.get(`/chats/user/${userId}`);
    return response.data;
  },
  createChat: async (userId, conversationName) => {
    const response = await api.post('/chats/new', { user_id: userId, conversation_name: conversationName });
    return response.data;
  },
  sendMessage: async (chatId, role, content) => {
    const response = await api.post(`/chats/${chatId}/message`, { role, content });
    return response.data;
  },
};

export const papersAPI = {
  search: async (query) => {
    // We pass the query as a URL parameter
    const response = await api.get('/papers/search', { params: { query } });
    return response.data;
  },
  attachPaper: async (chatId, arxivId, title) => {
    const response = await api.post(`/papers/${chatId}/attach`, { arxiv_id: arxivId, title: title });
    return response.data;
  }
};

export default api;