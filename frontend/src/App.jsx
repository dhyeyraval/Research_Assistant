import React, { useContext } from 'react';
import { UserContext } from './context/UserContext';
import Login from './components/Login';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';

function App() {
  const { user } = useContext(UserContext);

  // If no session exists, capture the username first
  if (!user) {
    return <Login />;
  }

  // Once authenticated, render full application environment
  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
      <ChatWindow />
    </div>
  );
}

export default App;