import React, { useState, useEffect } from 'react';
import { List, ListItem, ListItemText, Paper, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import axios from 'axios';

const ProactiveAlerts = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const fetchAlerts = async () => {
      const response = await axios.get('http://localhost:8000/alerts/proactive');
      setAlerts(response.data);
    };
    fetchAlerts();
  }, []);

  return (
    <Paper>
      <Typography variant="h4" sx={{ p: 2 }}>Proactive Alerts</Typography>
      <List>
        {alerts.map((alert, index) => (
          <ListItem key={index} button component={Link} to={`/account/${alert.account_id}`}>
            <ListItemText primary={alert.summary} />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default ProactiveAlerts;
