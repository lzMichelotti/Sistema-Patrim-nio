import React, { useState } from 'react';
import './ChatWidget.css';

const ChatWidget = ({ onNewItem }) => {
  const API_URL = import.meta.env.VITE_API_URL || '/api';
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Olá! Como posso ajudar com o patrimônio hoje?' }
  ]);
  const [loading, setLoading] = useState(false);

  const toggleChat = () => setIsOpen(!isOpen);

const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      
      // --- MUDANÇA AQUI ---
      // O Python agora retorna 'success' quando salva no banco.
      if (data.type === 'success') {
        
        setMessages((prev) => [...prev, { role: 'assistant', text: data.message }]);
        
        // CORREÇÃO: Passamos o objeto que veio do Python para a lista
        if (onNewItem) {
           onNewItem(data.data); 
        }

      } else {
        // Chat normal ou erro
        setMessages((prev) => [...prev, { role: 'assistant', text: data.message }]);
      }

    } catch (error) {
      console.error('Erro:', error);
      setMessages((prev) => [...prev, { role: 'assistant', text: 'Erro de conexão com o servidor.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-widget-container">
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <span>Assistente IA</span>
            <button onClick={toggleChat} className="close-btn">×</button>
          </div>
          
          <div className="chat-body">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="message assistant">Digitando...</div>}
          </div>

          <div className="chat-footer">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Digite seu comando..."
            />
            <button onClick={handleSend}>Enviar</button>
          </div>
        </div>
      )}

      {!isOpen && (
        <button className="chat-toggle-btn" onClick={toggleChat}>
          💬 IA
        </button>
      )}
    </div>
  );
};

export default ChatWidget;