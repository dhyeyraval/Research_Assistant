import React, { useState, useContext } from 'react';
import { UserContext } from '../context/UserContext';
import { papersAPI } from '../services/api';

export default function SearchBar() {
  const { activeChat, setActiveChat, setChats } = useContext(UserContext);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setIsOpen(true);
    try {
      const data = await papersAPI.search(query);
      setResults(data);
    } catch (error) {
      alert("Search failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const handleAttach = async (paper) => {
    if (!activeChat) return;
    try {
      const response = await papersAPI.attachPaper(activeChat.id, paper.arxiv_id, paper.title);
      
      // Update local context so the UI reflects the newly attached paper immediately
      const updatedChat = { ...activeChat, attached_papers: response.attached_papers };
      setActiveChat(updatedChat);
      setChats(prev => prev.map(c => c.id === activeChat.id ? updatedChat : c));
      
      // Close the dropdown and clear search
      setIsOpen(false);
      setQuery('');
    } catch (error) {
      alert("Failed to attach paper.");
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', marginBottom: '1rem' }}>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search arXiv for papers (e.g. Attention Is All You Need)"
          style={{ flex: 1, padding: '0.6rem', borderRadius: '4px', border: '1px solid #565869', background: '#40414F', color: '#fff' }}
        />
        <button type="submit" disabled={loading} style={{ padding: '0.6rem 1rem', cursor: 'pointer' }}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Dropdown Results Window */}
      {isOpen && (
        <div style={{ 
          position: 'absolute', top: '100%', left: 0, right: 0, 
          background: '#202123', border: '1px solid #565869', 
          maxHeight: '400px', overflowY: 'auto', zIndex: 10,
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)', marginTop: '4px', borderRadius: '4px'
        }}>
          <div style={{ padding: '8px', borderBottom: '1px solid #565869', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: '#aaa' }}>Search Results</span>
            <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: '#aaa', cursor: 'pointer' }}>Close (X)</button>
          </div>
          
          {results.length === 0 && !loading && (
             <div style={{ padding: '1rem', color: '#aaa', textAlign: 'center' }}>No results found.</div>
          )}

          {results.map((paper) => (
            <div key={paper.arxiv_id} style={{ padding: '1rem', borderBottom: '1px solid #343541' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#fff' }}>{paper.title}</h4>
              <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#aaa' }}>{paper.authors.join(', ')} | ID: {paper.arxiv_id}</p>
              
              <button 
                onClick={() => handleAttach(paper)}
                disabled={activeChat?.attached_papers?.some(p => p.arxiv_id === paper.arxiv_id)}
                style={{ 
                  background: activeChat?.attached_papers?.some(p => p.arxiv_id === paper.arxiv_id) ? '#343541' : '#10a37f', 
                  color: '#fff', border: 'none', padding: '4px 12px', borderRadius: '4px', cursor: 'pointer' 
                }}
              >
                {activeChat?.attached_papers?.some(p => p.arxiv_id === paper.arxiv_id) ? 'Already Attached' : 'Attach to Chat'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}