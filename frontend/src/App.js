import React, { useState, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Header from './components/Header';
import Overview from './pages/Overview';
import ProactiveAlerts from './pages/ProactiveAlerts';
import AccountDrilldown from './pages/AccountDrilldown';
import Chat from './pages/Chat';
import Settings from './pages/Settings';

const getDesignTokens = (mode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          // palette values for light mode
          primary: {
            main: '#1976d2',
          },
          secondary: {
            main: '#dc004e',
          },
          background: {
            default: '#f5f5f5',
            paper: '#ffffff',
          },
        }
      : {
          // palette values for dark mode
          primary: {
            main: '#90caf9',
          },
          secondary: {
            main: '#f48fb1',
          },
          background: {
            default: '#121212',
            paper: '#1e1e1e',
          },
        }),
  },
  typography: {
    fontFamily: 'Roboto, sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
  shadows: Array(25).fill('0px 4px 20px rgba(0, 0, 0, 0.3)'), // Deeper shadows
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12, // More rounded cards
          boxShadow: '0px 8px 25px rgba(0, 0, 0, 0.4)', // Even deeper shadow for cards
          transition: 'transform 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-5px)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 8px 25px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          borderRadius: 0, // Remove rounded edges for AppBar
        },
      },
    },
  },
});

function App() {
  const [mode, setMode] = useState('dark');
  const [chatOpen, setChatOpen] = useState(false);

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
      },
    }),
    [],
  );

  const theme = useMemo(() => createTheme(getDesignTokens(mode)), [mode]);

  const toggleChat = () => {
    setChatOpen(!chatOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          <Header toggleChat={toggleChat} toggleColorMode={colorMode.toggleColorMode} currentMode={mode} />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/alerts" element={<ProactiveAlerts />} />
              <Route path="/account/:accountId" element={<AccountDrilldown />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Box>
          <Chat open={chatOpen} toggleChat={toggleChat} />
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
