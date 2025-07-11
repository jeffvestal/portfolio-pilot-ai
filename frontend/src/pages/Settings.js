import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    TextField, 
    Button, 
    Paper, 
    Switch, 
    List, 
    ListItem, 
    ListItemText, 
    IconButton,
    Stack,
    FormControlLabel 
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const Settings = () => {
    const [settings, setSettings] = useState(null);
    const [newServerUrl, setNewServerUrl] = useState('');
    const [newServerApiKey, setNewServerApiKey] = useState('');
    const [newServerName, setNewServerName] = useState('');
    const [newServerUseForMainPage, setNewServerUseForMainPage] = useState(false);
    const [loggingEnabled, setLoggingEnabled] = useState(false);

    useEffect(() => {
        // Fetch server settings
        fetch('/settings')
            .then(res => res.json())
            .then(data => setSettings(data))
            .catch(err => console.error("Failed to fetch settings:", err));
        
        // Fetch logging status
        fetch('/settings/logging')
            .then(res => res.json())
            .then(data => setLoggingEnabled(data.enabled))
            .catch(err => console.error("Failed to fetch logging status:", err));
    }, []);

    const handleToggle = (server, tool = null) => {
        const newSettings = { ...settings };
        if (tool) {
            // Toggle individual tool
            newSettings[server].tools[tool].enabled = !newSettings[server].tools[tool].enabled;
        } else {
            // Toggle server and all its tools
            const serverEnabled = !newSettings[server].enabled;
            newSettings[server].enabled = serverEnabled;
            
            // Toggle all tools to match server state
            Object.keys(newSettings[server].tools || {}).forEach(toolName => {
                newSettings[server].tools[toolName].enabled = serverEnabled;
            });
        }
        setSettings(newSettings);
        fetch('/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSettings),
        });
    };

    const handleMainPageToggle = (serverId) => {
        const newSettings = { ...settings };
        const currentValue = newSettings[serverId].use_for_main_page || false;
        newSettings[serverId].use_for_main_page = !currentValue;
        
        setSettings(newSettings);
        
        // Update the server configuration on the backend
        fetch(`/servers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: serverId,
                name: newSettings[serverId].name,
                url: newSettings[serverId].url,
                apiKey: newSettings[serverId].api_key,
                useForMainPage: !currentValue
            }),
        }).catch(error => {
            console.error('Failed to update main page setting:', error);
            // Revert the change on error
            newSettings[serverId].use_for_main_page = currentValue;
            setSettings(newSettings);
        });
    };

    const handleAddServer = () => {
        const serverData = {
            id: 'new-server-' + Date.now(),
            name: newServerName,
            url: newServerUrl,
            apiKey: newServerApiKey,
            useForMainPage: newServerUseForMainPage
        };

        fetch('/servers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(serverData),
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => { throw new Error(err.detail || 'Server returned an error') });
            }
            return res.json();
        })
        .then(data => {
            const newSettings = { ...settings, [data.id]: data };
            setSettings(newSettings);
            setNewServerName('');
            setNewServerUrl('');
            setNewServerApiKey('');
            setNewServerUseForMainPage(false);
        })
        .catch(error => {
            console.error('Failed to add server:', error);
            alert(`Error adding server: ${error.message}`);
        });
    };

    const handleRemoveServer = (serverId) => {
        fetch(`/servers/${serverId}`, { method: 'DELETE' })
        .then(() => {
            const newSettings = { ...settings };
            delete newSettings[serverId];
            setSettings(newSettings);
        });
    };

    const handleLoggingToggle = (event) => {
        const isEnabled = event.target.checked;
        setLoggingEnabled(isEnabled);
        fetch('/settings/logging', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: isEnabled }),
        });
    };

    if (!settings) {
        return <Typography>Loading...</Typography>;
    }

    return (
        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <Typography variant="h4" gutterBottom>MCP Settings</Typography>
            
            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" gutterBottom>Register New Server</Typography>
                <Stack spacing={2} sx={{ mb: 2 }}>
                    <TextField
                        label="Server Name"
                        variant="outlined"
                        fullWidth
                        value={newServerName}
                        onChange={(e) => setNewServerName(e.target.value)}
                        placeholder="e.g., My Elasticsearch Server"
                    />
                    <TextField
                        label="Server URL"
                        variant="outlined"
                        fullWidth
                        value={newServerUrl}
                        onChange={(e) => setNewServerUrl(e.target.value)}
                        placeholder="e.g., http://localhost:5601"
                    />
                    <TextField
                        label="API Key (optional)"
                        variant="outlined"
                        fullWidth
                        type="password"
                        value={newServerApiKey}
                        onChange={(e) => setNewServerApiKey(e.target.value)}
                        placeholder="Enter API Key"
                    />
                    <FormControlLabel
                        control={
                            <Switch 
                                checked={newServerUseForMainPage}
                                onChange={(e) => setNewServerUseForMainPage(e.target.checked)}
                            />
                        }
                        label="Use for main page data"
                    />
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4, mt: -1 }}>
                        Enable this server to provide additional dashboard content like news summaries
                    </Typography>
                </Stack>
                <Button variant="contained" color="primary" onClick={handleAddServer}>
                    Add Server
                </Button>
            </Paper>

            <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" gutterBottom>Global Settings</Typography>
                <FormControlLabel
                    control={<Switch checked={loggingEnabled} onChange={handleLoggingToggle} />}
                    label="Enable MCP Communication Logging"
                />
            </Paper>

            {Object.entries(settings).map(([serverId, server]) => (
                <Paper key={serverId} sx={{ p: 3, mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h5">{server.name}</Typography>
                        <Box>
                            <Switch checked={server.enabled} onChange={() => handleToggle(serverId)} />
                            {serverId !== 'local' && (
                                <IconButton onClick={() => handleRemoveServer(serverId)} color="error">
                                    <DeleteIcon />
                                </IconButton>
                            )}
                        </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>{server.url}</Typography>
                    
                    <Box sx={{ mt: 2, mb: 2 }}>
                        <FormControlLabel
                            control={
                                <Switch 
                                    checked={server.use_for_main_page || false}
                                    onChange={() => handleMainPageToggle(serverId)}
                                    disabled={!server.enabled}
                                />
                            }
                            label="Use for main page data"
                            sx={{ opacity: server.enabled ? 1 : 0.5 }}
                        />
                        <Typography variant="caption" display="block" color="text.secondary" sx={{ ml: 4 }}>
                            When enabled, this server will provide additional content like news summaries for the dashboard
                        </Typography>
                    </Box>
                    
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="h6">Tools</Typography>
                        <List>
                            {Object.entries(server.tools || {}).map(([toolId, tool]) => (
                                <ListItem key={toolId} secondaryAction={
                                    <Switch 
                                        edge="end" 
                                        checked={server.enabled && (tool.enabled || false)} 
                                        disabled={!server.enabled}
                                        onChange={() => handleToggle(serverId, toolId)} 
                                    />
                                }>
                                    <ListItemText 
                                        primary={toolId} 
                                        secondary={tool.description || 'No description available'}
                                        sx={{ opacity: server.enabled ? 1 : 0.5 }}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                </Paper>
            ))}
        </Box>
    );
};

export default Settings;
