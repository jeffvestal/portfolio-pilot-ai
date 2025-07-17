import React from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Fade,
  Chip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import SettingsIcon from '@mui/icons-material/Settings';
import { useMCPNotification } from '../contexts/MCPNotificationContext';

const NotificationContainer = styled(Box)(({ theme }) => ({
  position: 'fixed',
  bottom: 20,
  left: 20,
  zIndex: 10000, // Increased z-index
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
  maxWidth: 300,
  pointerEvents: 'none', // Allow clicks to pass through
}));

const NotificationPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1, 2),
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  boxShadow: theme.shadows[6],
  borderRadius: theme.spacing(1),
  minWidth: 250,
  pointerEvents: 'auto', // Re-enable clicks on the notification itself
}));

const MCPToolNotification = () => {
  const { activeTools } = useMCPNotification();
  
  try {
    // Convert Map to array for rendering
    const toolsArray = Array.from(activeTools.entries()).map(([id, tool]) => ({
      id,
      ...tool
    }));

    console.log('🔧 MCP Notification Component: Rendering with', toolsArray.length, 'tools:', toolsArray);

    return (
      <NotificationContainer>
        {toolsArray.map((tool) => (
          <Fade key={tool.id} in={true} timeout={300}>
            <NotificationPaper elevation={6}>
              <CircularProgress 
                size={16} 
                thickness={4}
                sx={{ color: 'inherit' }}
              />
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
                  <SettingsIcon sx={{ fontSize: 14 }} />
                  <Typography variant="caption" fontWeight="bold">
                    MCP Tool
                  </Typography>
                </Box>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontSize: '0.75rem',
                    lineHeight: 1.2,
                    wordBreak: 'break-word'
                  }}
                >
                  {tool.toolName}
                </Typography>
                {tool.description && (
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontSize: '0.7rem',
                      opacity: 0.9,
                      display: 'block',
                      lineHeight: 1.1
                    }}
                  >
                    {tool.description}
                  </Typography>
                )}
              </Box>
              <Chip 
                label="Active" 
                size="small" 
                variant="outlined"
                sx={{ 
                  fontSize: '0.6rem',
                  height: 20,
                  borderColor: 'currentColor',
                  color: 'inherit'
                }}
              />
            </NotificationPaper>
          </Fade>
        ))}
      </NotificationContainer>
    );
  } catch (error) {
    console.error('🔧 MCP Notification Component Error:', error);
    return (
      <Box 
        sx={{ 
          position: 'fixed', 
          bottom: 20, 
          left: 20, 
          zIndex: 10000,
          backgroundColor: 'red',
          color: 'white',
          p: 1,
          borderRadius: 1
        }}
      >
        MCP Notification Error
      </Box>
    );
  }
};

export default MCPToolNotification;