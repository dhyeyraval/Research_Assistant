import React, { createContext, useState, useEffect } from 'react';
import { chatsAPI } from '../services/api';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('research_user');
    return saved ? JSON.parse(saved) : null;
  });
  
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [loadingChats, setLoadingChats] = useState(false);

  // Fetch conversations whenever the user logs in or changes
  useEffect(() => {
    if (user?.id) {
      fetchUserChats(user.id);
    } else {
      setChats([]);
      setActiveChat(null);
    }
  }, [user]);

  const fetchUserChats = async (userId) => {
    setLoadingChats(true);
    try {
      const data = await chatsAPI.getUserChats(userId);
      setChats(data);
      if (data.length > 0 && !activeChat) {
        setActiveChat(data[0]); // Auto-select the most recent chat
      }
    } catch (error) {
      print("Error fetching user chats:", error);
    } finally {
      setLoadingChats(false);
    }
  };

  const createNewConversation = async (name) => {
    if (!user?.id) return;
    try {
      const newChat = await chatsAPI.createChat(user.id, name);
      setChats((prev) => [newChat, ...prev]);
      setActiveChat(newChat);
      return newChat;
    } catch (error) {
      print("Error creating conversation:", error);
    }
  };

  const logout = () => {
    localStorage.removeItem('research_user');
    setUser(null);
  };

  return (
    <UserContext.Provider value={{
      user,
      setUser,
      chats,
      setChats,
      activeChat,
      setActiveChat,
      loadingChats,
      createNewConversation,
      fetchUserChats,
      logout
    }}>
      {children}
    </UserContext.Provider>
  );
};