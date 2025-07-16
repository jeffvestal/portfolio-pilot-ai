import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton } from '@mui/material';
import { Link } from 'react-router-dom';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import SettingsIcon from '@mui/icons-material/Settings';

const Header = ({ toggleChat, toggleColorMode, currentMode }) => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Portfolio-Pilot-AI
        </Typography>
        <Box>
          <Button color="inherit" component={Link} to="/">Overview</Button>
          <Button color="inherit" component={Link} to="/alerts">Negative News</Button>
          <Button color="inherit" onClick={toggleChat}>Chat</Button>
          <IconButton sx={{ ml: 1 }} onClick={toggleColorMode} color="inherit">
            {currentMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
          <IconButton sx={{ ml: 1 }} component={Link} to="/settings" color="inherit">
            <SettingsIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
