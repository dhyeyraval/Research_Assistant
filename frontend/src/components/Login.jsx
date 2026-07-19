import React, { useState, useContext } from 'react';
import { UserContext } from '../context/UserContext';
import { authAPI } from '../services/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const { setUser } = useContext(UserContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(false);
    try {
      const userData = await authAPI.loginOrCreate(username.trim());
      localStorage.setItem('research_user', JSON.stringify(userData));
      setUser(userData);
    } catch (error) {
      alert("Failed to sign in. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: '#343541', color: '#ececf1' }}>
      <form onSubmit={handleSubmit} style={{ background: '#202123', padding: '2rem', borderRadius: '8px', border: '1px solid #4d4d4f', boxShadow: '0 8px 24px rgba(0,0,0,0.35)', width: '320px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem', color: '#ececf1' }}>Research Assistant</h3>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#aaa' }}>Enter Username</label>
        <input 
          type="text" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g., researcher_1" 
          style={{ width: '100%', padding: '0.65rem', marginBottom: '1rem', boxSizing: 'border-box', background: '#40414F', border: '1px solid #565869', color: '#fff', borderRadius: '4px' }}
          required 
        />
        <button type="submit" disabled={loading} style={{ width: '100%', padding: '0.65rem', cursor: 'pointer', background: '#40414F', border: '1px solid #565869', color: '#ececf1', borderRadius: '4px' }}>
          {loading ? 'Entering...' : 'Enter App'}
        </button>
      </form>
    </div>
  );
}