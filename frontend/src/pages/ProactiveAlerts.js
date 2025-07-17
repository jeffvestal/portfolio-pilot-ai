import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Box,
  Chip,
  Grid,
  Button,
  Divider,
  Collapse
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TimePeriodSelector from '../components/TimePeriodSelector';
import { useMCPNotification } from '../contexts/MCPNotificationContext';
import axios from 'axios';

const ProactiveAlerts = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showMCPTool, hideMCPTool } = useMCPNotification();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timePeriod, setTimePeriod] = useState(48);
  const [timeUnit, setTimeUnit] = useState('hours');
  const [expandedAlerts, setExpandedAlerts] = useState(new Set());
  const [lastFetchedTimePeriod, setLastFetchedTimePeriod] = useState(48);
  const [lastFetchedTimeUnit, setLastFetchedTimeUnit] = useState('hours');

  useEffect(() => {
    // Check if we have preserved state from navigation
    const preservedState = location.state;
    if (preservedState?.preserveState && preservedState.alertsData) {
      // Restore preserved state
      setAlerts(preservedState.alertsData);
      setTimePeriod(preservedState.timePeriod || 48);
      setTimeUnit(preservedState.timeUnit || 'hours');
      setExpandedAlerts(new Set(preservedState.expandedAlerts || []));
      setLoading(false);
      
      // Clear the state to prevent issues with browser back button
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      // Normal fetch when time period changes or on initial load
      fetchAlerts();
    }
  }, []);

  // Remove automatic refresh on time period changes - now manual only

  const fetchAlerts = async () => {
    const notificationId = showMCPTool('neg_news_reports_with_pos', 'Finding negative news affecting portfolio positions');
    
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `http://localhost:8000/alerts/negative-news?time_period=${timePeriod}&time_unit=${timeUnit}`
      );
      setAlerts(response.data);
      // Track last fetched values for button state
      setLastFetchedTimePeriod(timePeriod);
      setLastFetchedTimeUnit(timeUnit);
    } catch (err) {
      console.error('Error fetching negative news alerts:', err);
      setError('Failed to load negative news alerts');
    } finally {
      setLoading(false);
      hideMCPTool(notificationId);
    }
  };

  const handleAccountClick = (accountId) => {
    if (accountId) {
      // Pass current state to preserve when returning
      navigate(`/account/${accountId}`, {
        state: {
          fromAlerts: true,
          alertsData: alerts,
          timePeriod: timePeriod,
          timeUnit: timeUnit,
          expandedAlerts: Array.from(expandedAlerts)
        }
      });
    }
  };

  const handleToggleExpand = (index) => {
    const newExpanded = new Set(expandedAlerts);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedAlerts(newExpanded);
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const renderServerError = () => {
    if (alerts.status === 'no_servers') {
      return (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            No MCP Servers Configured
          </Typography>
          <Typography>
            {alerts.message}
          </Typography>
        </Alert>
      );
    }

    if (alerts.status === 'tool_not_available') {
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Required Server Not Connected
          </Typography>
          <Typography>
            The MCP server required for negative news analysis is not connected or does not support the required tool (neg_news_reports_with_pos). 
            Please check your MCP server configuration.
          </Typography>
        </Alert>
      );
    }

    if (alerts.status === 'error') {
      return (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Error Loading Alerts
          </Typography>
          <Typography>
            {alerts.message}
          </Typography>
        </Alert>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingDownIcon sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="h4" component="h1">
                Negative News Alerts
              </Typography>
            </Box>
            <Typography variant="subtitle1" color="textSecondary">
              Monitor accounts with positions affected by negative sentiment news
            </Typography>
          </CardContent>
        </Card>
        
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <TrendingDownIcon sx={{ mr: 1, color: 'error.main' }} />
            <Typography variant="h4" component="h1">
              Negative News Alerts
            </Typography>
          </Box>
          
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Monitor accounts with positions affected by negative sentiment news
          </Typography>

          <Box mt={3} display="flex" alignItems="center" gap={2} flexWrap="wrap">
            <TimePeriodSelector
              timePeriod={timePeriod}
              timeUnit={timeUnit}
              onTimePeriodChange={setTimePeriod}
              onTimeUnitChange={setTimeUnit}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={fetchAlerts}
              disabled={loading || (timePeriod === lastFetchedTimePeriod && timeUnit === lastFetchedTimeUnit)}
              sx={{ ml: 2 }}
            >
              Check Time Range
            </Button>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {renderServerError()}

      {alerts.status === 'success' && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Alert Summary
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip 
                  label={`${alerts.alerts?.length || 0} News Stories`} 
                  color="primary" 
                />
                <Chip 
                  label={`${alerts.alerts?.reduce((sum, story) => sum + story.total_accounts_affected, 0) || 0} Total Accounts Affected`} 
                  color="warning" 
                />
                <Chip 
                  label={`Source: ${alerts.server_used}`} 
                  variant="outlined" 
                />
                <Chip 
                  label={`Period: ${timePeriod} ${timeUnit}`} 
                  variant="outlined" 
                />
              </Box>
            </CardContent>
          </Card>

          <Grid container spacing={3}>
            {alerts.alerts?.map((story, storyIndex) => (
              <Grid item xs={12} key={storyIndex}>
                <Card 
                  sx={{ 
                    borderLeft: `4px solid ${
                      story.severity === 'high' ? '#f44336' : 
                      story.severity === 'medium' ? '#ff9800' : '#2196f3'
                    }` 
                  }}
                >
                  <CardContent>
                    {/* News Story Header */}
                    <Box display="flex" justifyContent="between" alignItems="flex-start" mb={2}>
                      <Box sx={{ flexGrow: 1, pr: 2 }}>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          {getSeverityIcon(story.severity)}
                          <Typography variant="h6" component="h3">
                            {story.news_title || 'Negative News Alert'}
                          </Typography>
                          <Chip 
                            label={story.severity?.toUpperCase() || 'UNKNOWN'} 
                            size="small" 
                            color={getSeverityColor(story.severity)} 
                          />
                        </Box>
                        
                        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                          {story.symbol && (
                            <Chip label={story.symbol} size="small" color="primary" />
                          )}
                          {story.news_source && (
                            <Chip label={story.news_source} size="small" variant="outlined" />
                          )}
                          <Chip 
                            label={`${story.total_accounts_affected} accounts affected`} 
                            size="small" 
                            color="warning" 
                          />
                        </Box>
                      </Box>
                      
                      {story.published_date && (
                        <Typography variant="caption" color="textSecondary">
                          {formatDate(story.published_date)}
                        </Typography>
                      )}
                    </Box>

                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {story.news_summary}
                    </Typography>

                    {/* Story Summary Stats */}
                    <Box sx={{ mb: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="textSecondary">
                            Total Exposure
                          </Typography>
                          <Typography variant="h6" color="error.main">
                            {formatCurrency(story.total_exposure)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="textSecondary">
                            Accounts
                          </Typography>
                          <Typography variant="h6">
                            {story.total_accounts_affected}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="textSecondary">
                            Avg Position
                          </Typography>
                          <Typography variant="h6">
                            {formatCurrency(story.total_exposure / story.total_accounts_affected)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="textSecondary">
                            Symbol
                          </Typography>
                          <Typography variant="h6">
                            {story.symbol || 'Multiple'}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Affected Accounts Section */}
                    <Box>
                      <Typography variant="subtitle1" gutterBottom>
                        Affected Accounts ({story.total_accounts_affected})
                      </Typography>
                      
                      {story.affected_accounts?.slice(0, 3).map((account, accountIndex) => (
                        <Box 
                          key={accountIndex} 
                          sx={{ 
                            mb: 2, 
                            p: 2, 
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1 
                          }}
                        >
                          <Box mb={2}>
                            <Typography variant="subtitle2" fontWeight="bold" mb={1}>
                              {account.account_name || account.account_id}
                            </Typography>
                            <Box>
                              <Typography variant="caption" color="textSecondary">
                                Position Value
                              </Typography>
                              <Typography variant="h6" color="success.main" fontWeight="medium">
                                {formatCurrency(account.current_value || account.basic_position_value)}
                              </Typography>
                            </Box>
                          </Box>
                          
                          {account.quantity && (
                            <Grid container spacing={1} sx={{ mt: 1 }}>
                              <Grid item xs={6} sm={3}>
                                <Typography variant="caption" color="textSecondary">
                                  Quantity
                                </Typography>
                                <Typography variant="body2">
                                  {account.quantity?.toLocaleString()}
                                </Typography>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Typography variant="caption" color="textSecondary">
                                  Avg Cost
                                </Typography>
                                <Typography variant="body2">
                                  {formatCurrency(account.purchase_price)}
                                </Typography>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Typography variant="caption" color="textSecondary">
                                  Current Price
                                </Typography>
                                <Typography variant="body2">
                                  {formatCurrency(account.current_price)}
                                </Typography>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Typography variant="caption" color="textSecondary">
                                  P&L
                                </Typography>
                                <Typography 
                                  variant="body2" 
                                  color={account.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                                >
                                  {formatCurrency(account.unrealized_pnl)} ({account.unrealized_pnl_pct?.toFixed(1)}%)
                                </Typography>
                              </Grid>
                            </Grid>
                          )}
                          
                          <Box sx={{ mt: 1 }}>
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<AccountBalanceIcon />}
                              onClick={() => handleAccountClick(account.account_id)}
                            >
                              View Account Details
                            </Button>
                          </Box>
                        </Box>
                      ))}
                      
                      {story.affected_accounts?.length > 3 && (
                        <Collapse in={expandedAlerts.has(storyIndex)}>
                          {story.affected_accounts?.slice(3).map((account, accountIndex) => (
                            <Box 
                              key={accountIndex + 3} 
                              sx={{ 
                                mb: 2, 
                                p: 2, 
                                border: '1px solid',
                                borderColor: 'divider',
                                borderRadius: 1 
                              }}
                            >
                              <Box mb={2}>
                                <Typography variant="subtitle2" fontWeight="bold" mb={1}>
                                  {account.account_name || account.account_id}
                                </Typography>
                                <Box>
                                  <Typography variant="caption" color="textSecondary">
                                    Position Value
                                  </Typography>
                                  <Typography variant="h6" color="success.main" fontWeight="medium">
                                    {formatCurrency(account.current_value || account.basic_position_value)}
                                  </Typography>
                                </Box>
                              </Box>
                              
                              {account.quantity && (
                                <Grid container spacing={1} sx={{ mt: 1 }}>
                                  <Grid item xs={6} sm={3}>
                                    <Typography variant="caption" color="textSecondary">
                                      Quantity
                                    </Typography>
                                    <Typography variant="body2">
                                      {account.quantity?.toLocaleString()}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={6} sm={3}>
                                    <Typography variant="caption" color="textSecondary">
                                      Avg Cost
                                    </Typography>
                                    <Typography variant="body2">
                                      {formatCurrency(account.purchase_price)}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={6} sm={3}>
                                    <Typography variant="caption" color="textSecondary">
                                      Current Price
                                    </Typography>
                                    <Typography variant="body2">
                                      {formatCurrency(account.current_price)}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={6} sm={3}>
                                    <Typography variant="caption" color="textSecondary">
                                      P&L
                                    </Typography>
                                    <Typography 
                                      variant="body2" 
                                      color={account.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                                    >
                                      {formatCurrency(account.unrealized_pnl)} ({account.unrealized_pnl_pct?.toFixed(1)}%)
                                    </Typography>
                                  </Grid>
                                </Grid>
                              )}
                              
                              <Box sx={{ mt: 1 }}>
                                <Button
                                  variant="outlined"
                                  size="small"
                                  startIcon={<AccountBalanceIcon />}
                                  onClick={() => handleAccountClick(account.account_id)}
                                >
                                  View Account Details
                                </Button>
                              </Box>
                            </Box>
                          ))}
                        </Collapse>
                      )}
                    </Box>

                    {/* Show More/Less Button */}
                    {story.affected_accounts?.length > 3 && (
                      <Box sx={{ mt: 2 }}>
                        <Button
                          variant="text"
                          size="small"
                          startIcon={expandedAlerts.has(storyIndex) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          onClick={() => handleToggleExpand(storyIndex)}
                        >
                          {expandedAlerts.has(storyIndex) 
                            ? 'Show Less Accounts' 
                            : `Show ${story.affected_accounts.length - 3} More Accounts`}
                        </Button>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {alerts.status === 'no_data' && (
        <Card>
          <CardContent>
            <Box display="flex" flexDirection="column" alignItems="center" py={4}>
              <InfoIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Negative News Alerts
              </Typography>
              <Typography variant="body2" color="textSecondary" textAlign="center">
                No accounts with positions affected by negative sentiment news found in the last {timePeriod} {timeUnit}.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProactiveAlerts;