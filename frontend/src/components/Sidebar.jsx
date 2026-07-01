import React, { useContext, useState } from 'react';
import { UserContext } from '../context/UserContext';

export default function Sidebar() {
  const { user, chats, activeChat, setActiveChat, createNewConversation, logout } = useContext(UserContext);
  const [newChatName, setNewChatName] = useState('');

  const handleCreateChat = (e) => {
    e.preventDefault();
    if (!newChatName.trim()) return;
    createNewConversation(newChatName.trim());
    setNewChatName('');
  };

  return (
    <div style={{ width: '260px', background: '#202123', color: '#fff', display: 'flex', flexDirection: 'column', height: '100vh', padding: '1rem', boxSizing: 'border-box' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <strong>User: {user?.username}</strong>
        <button onClick={logout} style={{ marginLeft: '10px', fontSize: '11px', cursor: 'pointer' }}>Logout</button>
      </div>

      <form onSubmit={handleCreateChat} style={{ marginBottom: '1rem' }}>
        <input 
          type="text" 
          placeholder="+ New Chat Name" 
          value={newChatName} 
          onChange={(e) => setNewChatName(e.target.value)}
          style={{ width: '100%', padding: '0.4rem', background: '#40414F', border: 'none', color: '#fff', boxSizing: 'border-box' }}
        />
      </form>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        <h4>Conversations</h4>
        {chats.map((chat) => (
          <div 
            key={chat.id} 
            onClick={() => setActiveChat(chat)}
            style={{ 
              padding: '0.6rem', 
              cursor: 'pointer', 
              background: activeChat?.id === chat.id ? '#343541' : 'transparent',
              borderRadius: '4px',
              marginBottom: '4px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            💬 {chat.conversation_name}
          </div>
        ))}
      </div>
    </div>
  );
}