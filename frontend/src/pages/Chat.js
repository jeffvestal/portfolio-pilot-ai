import React, { useState, useEffect, useRef } from 'react';
import { TextField, Button, Box, Paper, Typography, Drawer, IconButton, CircularProgress, Chip } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import ReactMarkdown from 'react-markdown';

const Chat = ({ open, toggleChat }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatWidth, setChatWidth] = useState(400); // Initial width
  const [sessionId, setSessionId] = useState(null); // Track conversation session
  const [isNewConversation, setIsNewConversation] = useState(true); // Flag for new conversations
  const isResizing = useRef(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Extract session ID from response text and clean the display text
  const extractSessionId = (responseText) => {
    const sessionMatch = responseText.match(/Session ID: ([a-f0-9-]+)/);
    if (sessionMatch) {
      const extractedSessionId = sessionMatch[1];
      console.log('📋 Extracted session ID:', extractedSessionId);
      setSessionId(extractedSessionId);
      setIsNewConversation(false);
      // Remove session ID from display text
      return responseText.replace(/Session ID: [a-f0-9-]+\n\n/, '');
    }
    return responseText;
  };

  // Start a new conversation
  const startNewConversation = () => {
    setSessionId(null);
    setIsNewConversation(true);
    setMessages([]);
  };

  // Reset session when chat is closed and reopened
  useEffect(() => {
    if (open) {
      // Chat is opening - optionally keep session
    } else {
      // Chat is closing - optionally reset session for fresh start next time
      // Uncomment the line below if you want to reset session on close:
      // startNewConversation();
    }
  }, [open]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: 'user', text: input, timestamp: new Date().toLocaleTimeString() };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    // Add a placeholder for the agent's message that we will update
    setMessages(prevMessages => [...prevMessages, { sender: 'agent', text: '', timestamp: new Date().toLocaleTimeString() }]);

    try {
      // Prepare request body with session ID if available
      const requestBody = { query: input };
      if (sessionId && !isNewConversation) {
        requestBody.session_id = sessionId;
        console.log('🔄 Sending request with session ID:', sessionId);
      } else {
        console.log('🆕 Sending new conversation request');
      }

      const response = await fetch('http://localhost:8000/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Await the full text response. This is simpler and more robust.
      const fullText = await response.text();

      // Extract session ID and clean display text
      const cleanedText = extractSessionId(fullText);

      // Update the last message with the cleaned text.
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages.length > 0 && newMessages[newMessages.length - 1].sender === 'agent') {
          newMessages[newMessages.length - 1].text = cleanedText;
        }
        return newMessages;
      });

    } catch (error) {
      console.error("Error fetching chat response:", error);
      const errorText = "Sorry, an error occurred while fetching the response.";
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages.length > 0 && newMessages[newMessages.length - 1].sender === 'agent') {
            newMessages[newMessages.length - 1].text = errorText;
        }
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        toggleChat();
      }
    };
    window.addEventListener('keydown', handleEsc);

    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, [toggleChat]);

  const handleMouseDown = (e) => {
    isResizing.current = true;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    if (!isResizing.current) return;
    const newWidth = window.innerWidth - e.clientX;
    setChatWidth(Math.max(300, Math.min(800, newWidth))); // Constrain width
  };

  const handleMouseUp = () => {
    isResizing.current = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      hideBackdrop={true}
      disableEscapeKeyDown={true}
      PaperProps={{
        sx: {
          width: chatWidth,
          boxShadow: '0px 8px 25px rgba(0, 0, 0, 0.4)',
          borderRadius: '12px 0 0 12px',
          overflow: 'hidden',
        },
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '10px',
          cursor: 'ew-resize',
          bgcolor: 'rgba(255, 255, 255, 0.1)',
          '&:hover': {
            bgcolor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
        onMouseDown={handleMouseDown}
      />
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, borderBottom: '1px solid #333' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <Typography variant="h6">Chat with AI</Typography>
            {sessionId && (
              <Chip 
                label={`Session: ${sessionId.slice(-8)}`} 
                size="small" 
                variant="outlined" 
                sx={{ mt: 0.5, fontSize: '0.7rem' }}
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              onClick={startNewConversation} 
              size="small"
              title="New Conversation"
            >
              <AddIcon />
            </IconButton>
            <IconButton onClick={toggleChat}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
        <Paper sx={{ flexGrow: 1, p: 2, overflowY: 'auto', bgcolor: 'background.default' }}>
          {messages.map((message, index) => (
            <Box key={index} sx={{ mb: 2, textAlign: message.sender === 'user' ? 'right' : 'left' }}>
              <Typography variant="caption" display="block" sx={{ color: 'text.secondary' }}>
                {message.sender === 'user' ? 'You' : 'AI Agent'} - {message.timestamp}
              </Typography>
              <Paper
                sx={{
                  display: 'inline-block',
                  p: 1,
                  bgcolor: message.sender === 'user' ? 'primary.dark' : 'background.paper',
                  borderRadius: '10px',
                  boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.2)',
                }}
              >
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </Paper>
            </Box>
          ))}
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 2 }}>
              <CircularProgress size={24} />
              <Typography sx={{ ml: 1, color: 'text.secondary' }}>AI is thinking...</Typography>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Paper>
        <Box sx={{ display: 'flex', p: 1, borderTop: '1px solid #333' }}>
          <TextField
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question..."
            disabled={isLoading}
          />
          <Button onClick={handleSend} sx={{ ml: 1 }} disabled={isLoading}>Send</Button>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Chat;
