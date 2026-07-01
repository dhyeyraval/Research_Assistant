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
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
      <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '2rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', width: '320px' }}>
        <h3>Research Assistant</h3>
        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Enter Username</label>
        <input 
          type="text" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)}
          placeholder="e.g., researcher_1" 
          style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', boxSizing: 'border-box' }}
          required 
        />
        <button type="submit" disabled={loading} style={{ width: '100%', padding: '0.5rem', cursor: 'pointer' }}>
          {loading ? 'Entering...' : 'Enter App'}
        </button>
      </form>
    </div>
  );
}