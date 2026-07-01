import React, { useContext, useState } from 'react';
import { UserContext } from '../context/UserContext';
import { chatsAPI } from '../services/api';
import SearchBar from './SearchBar';

export default function ChatWindow() {
  const { activeChat, setActiveChat, setChats } = useContext(UserContext);
  const [input, setInput] = useState('');

  if (!activeChat) {
    return <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#343541', color: '#aaa' }}>Select or create a conversation to begin.</div>;
  }

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessageText = input.trim();
    setInput('');

    // Optimistically update local active chat state before hitting server
    const localUserMsg = { role: 'user', content: userMessageText, timestamp: new Date().toISOString() };
    const updatedMessages = [...activeChat.messages, localUserMsg];
    
    setActiveChat({ ...activeChat, messages: updatedMessages });

    try {
      // Send user message to database
      await chatsAPI.sendMessage(activeChat.id, 'user', userMessageText);

      // Simple echo simulation for Phase 1 verification
      const assistantReplyText = `Echoing: "${userMessageText}". Data systems verified!`;
      const finalMessages = await chatsAPI.sendMessage(activeChat.id, 'assistant', assistantReplyText);

      // Sync backend updated list with context
      const updatedChatObj = { ...activeChat, messages: finalMessages };
      setActiveChat(updatedChatObj);
      setChats((prev) => prev.map(c => c.id === activeChat.id ? updatedChatObj : c));
    } catch (error) {
      alert("Failed to sync message with backend server.");
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', background: '#343541', color: '#ececf1' }}>
      
      {/* Header Area */}
      <div style={{ padding: '1rem', borderBottom: '1px solid #4d4d4f', background: '#202123' }}>
        <h3 style={{ margin: '0 0 1rem 0' }}>{activeChat.conversation_name}</h3>
        
        {/* Inject the Search Bar here */}
        <SearchBar />

        {/* Display Attached Papers */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#aaa' }}>Attached Papers:</span>
          {!activeChat.attached_papers || activeChat.attached_papers.length === 0 ? (
            <span style={{ fontSize: '12px', color: '#666' }}>None yet.</span>
          ) : (
            activeChat.attached_papers.map(paper => (
              <span 
                key={paper.arxiv_id} 
                title={paper.arxiv_id} // Hovering shows the ID!
                style={{ 
                  background: '#444654', 
                  padding: '4px 10px', 
                  borderRadius: '12px', 
                  fontSize: '12px',
                  maxWidth: '300px', // Prevents massive titles from breaking the UI
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {paper.title}
              </span>
            ))
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {activeChat.messages.map((msg, index) => (
          <div key={index} style={{ marginBottom: '1rem', padding: '0.5rem', background: msg.role === 'user' ? 'transparent' : '#444654', borderRadius: '4px' }}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
            <p style={{ margin: '4px 0 0 0' }}>{msg.content}</p>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} style={{ padding: '1rem', background: '#40414F' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the attached papers..." 
          style={{ width: '100%', padding: '0.8rem', background: '#40414F', border: '1px solid #565869', color: '#fff', borderRadius: '4px', boxSizing: 'border-box' }}
        />
      </form>
    </div>
  );
}