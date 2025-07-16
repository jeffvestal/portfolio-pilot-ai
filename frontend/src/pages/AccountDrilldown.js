import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Button, Card, CardContent, Grid, Typography, Modal, Box, TextField, List, ListItem, ListItemText, Collapse, CircularProgress, Alert, Chip } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import axios from 'axios';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 600,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  maxHeight: '80vh',
  overflowY: 'auto',
};

const AccountDrilldown = () => {
  const { accountId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [account, setAccount] = useState(null);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [email, setEmail] = useState({ subject: '', body: '' });
  const [articleModalOpen, setArticleModalOpen] = useState(false);
  const [articleContent, setArticleContent] = useState('');
  const [newsReports, setNewsReports] = useState(null);
  const [newsReportsLoading, setNewsReportsLoading] = useState(false);
  const [newsReportsError, setNewsReportsError] = useState(null);
  const [expandedArticles, setExpandedArticles] = useState(new Set());
  const [summaries, setSummaries] = useState(new Map());
  const [summarizingArticles, setSummarizingArticles] = useState(new Set());

  useEffect(() => {
    const fetchAccount = async () => {
      const response = await axios.get(`http://localhost:8000/account/${accountId}`);
      setAccount(response.data);
    };
    fetchAccount();
  }, [accountId]);

  useEffect(() => {
    const fetchNewsReports = async () => {
      setNewsReportsLoading(true);
      setNewsReportsError(null);
      try {
        const response = await axios.get(`http://localhost:8000/account/${accountId}/news-reports?time_period=72&time_unit=hours`);
        setNewsReports(response.data);
      } catch (err) {
        console.error('Error fetching news/reports:', err);
        setNewsReportsError('Failed to load news and reports');
      } finally {
        setNewsReportsLoading(false);
      }
    };

    if (accountId) {
      fetchNewsReports();
    }
  }, [accountId]);

  const handleEmailModalOpen = async (articleId) => {
    const response = await axios.post('http://localhost:8000/email/draft', { 
      account_id: accountId,
      article_id: articleId 
    });
    setEmail(response.data);
    setEmailModalOpen(true);
  };

  const handleEmailModalClose = () => setEmailModalOpen(false);

  const handleArticleOpen = async (articleId, type) => {
    try {
      const endpoint = type === 'news' ? `/article/${articleId}` : `/report/${articleId}`;
      const response = await axios.get(`http://localhost:8000${endpoint}`);
      setArticleContent(response.data.content);
      setArticleModalOpen(true);
    } catch (error) {
      console.error("Error fetching article/report content:", error);
      setArticleContent("Could not load content.");
      setArticleModalOpen(true);
    }
  };

  const handleArticleClose = () => {
    setArticleModalOpen(false);
    setArticleContent('');
  };

  const handleBackToAlerts = () => {
    // Check if we came from alerts page and preserve state
    const fromAlerts = location.state?.fromAlerts;
    if (fromAlerts) {
      navigate('/alerts', { 
        state: { 
          preserveState: true,
          alertsData: location.state.alertsData,
          timePeriod: location.state.timePeriod,
          timeUnit: location.state.timeUnit,
          expandedAlerts: location.state.expandedAlerts
        } 
      });
    } else {
      // Fallback to normal navigation
      navigate('/alerts');
    }
  };

  const handleToggleArticle = (articleIndex) => {
    const newExpanded = new Set(expandedArticles);
    if (newExpanded.has(articleIndex)) {
      newExpanded.delete(articleIndex);
    } else {
      newExpanded.add(articleIndex);
    }
    setExpandedArticles(newExpanded);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'default';
    const sent = sentiment.toLowerCase();
    if (sent.includes('positive')) return 'success';
    if (sent.includes('negative')) return 'error';
    if (sent.includes('neutral')) return 'warning';
    return 'default';
  };

  const getSentimentLabel = (sentiment) => {
    if (!sentiment) return 'Unknown';
    const sent = sentiment.toLowerCase();
    if (sent.includes('positive')) return 'Positive';
    if (sent.includes('negative')) return 'Negative'; 
    if (sent.includes('neutral')) return 'Neutral';
    return sentiment;
  };

  const handleSummarizeArticle = async (article, articleIndex) => {
    if (summaries.has(articleIndex)) {
      // If summary already exists, don't regenerate
      return;
    }

    // Add to summarizing set
    setSummarizingArticles(prev => new Set(prev).add(articleIndex));

    try {
      const response = await fetch('http://localhost:8000/article/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          article_content: article.content || article.summary || '',
          symbol: article.symbol || '',
          account_id: accountId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      let summary = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = new TextDecoder().decode(value);
        summary += chunk;
        
        // Update summary in real-time as it streams
        setSummaries(prev => new Map(prev).set(articleIndex, summary));
      }

    } catch (error) {
      console.error('Error summarizing article:', error);
      setSummaries(prev => new Map(prev).set(articleIndex, 'Error generating summary. Please try again.'));
    } finally {
      // Remove from summarizing set
      setSummarizingArticles(prev => {
        const newSet = new Set(prev);
        newSet.delete(articleIndex);
        return newSet;
      });
    }
  };

  if (!account) return <div>Loading...</div>;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Box sx={{ mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={handleBackToAlerts}
            sx={{ mb: 2 }}
          >
            Back to Alerts
          </Button>
        </Box>
        <Typography variant="h4">{account.account_name}</Typography>
        <Typography variant="subtitle1">{account.state} - {account.type} - {account.risk_profile}</Typography>
      </Grid>
      <Grid item xs={12}>
        <Button variant="contained" onClick={() => handleEmailModalOpen(account.relevant_news.articles[0].id)}>Draft Email</Button>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Holdings</Typography>
            {account.holdings.map((holding, index) => (
              <Box 
                key={index} 
                sx={{ 
                  mb: 2, 
                  p: 2, 
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  backgroundColor: 'background.paper'
                }}
              >
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  {holding.symbol} - {holding.company_name}
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="textSecondary">
                      Shares
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {holding.total_quantity?.toLocaleString()}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="textSecondary">
                      Total Value
                    </Typography>
                    <Typography variant="body1" fontWeight="medium" color="success.main">
                      ${holding.total_current_value?.toLocaleString()}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="textSecondary">
                      Sector
                    </Typography>
                    <Typography variant="body1">
                      {holding.sector}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Relevant News & Reports</Typography>
            
            {newsReportsLoading && (
              <Box display="flex" justifyContent="center" alignItems="center" py={4}>
                <CircularProgress size={40} />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  Loading news and reports for account symbols...
                </Typography>
              </Box>
            )}
            
            {newsReportsError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {newsReportsError}
              </Alert>
            )}
            
            {newsReports && newsReports.status === 'no_servers' && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  No MCP Servers Configured
                </Typography>
                <Typography variant="body2">
                  {newsReports.message}
                </Typography>
              </Alert>
            )}
            
            {newsReports && newsReports.status === 'tool_not_available' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Required Tool Not Available
                </Typography>
                <Typography variant="body2">
                  The MCP server does not support the news/reports lookup tool.
                </Typography>
              </Alert>
            )}
            
            {newsReports && newsReports.status === 'no_data' && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  No Recent News or Reports
                </Typography>
                <Typography variant="body2">
                  No news or reports found for this account's symbols in the last 72 hours.
                </Typography>
              </Alert>
            )}
            
            {newsReports && newsReports.status === 'success' && (
              <>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Found {newsReports.articles?.length || 0} articles for symbols: {newsReports.symbols_searched?.join(', ')}
                  </Typography>
                </Box>
                
                {newsReports.articles?.map((article, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Card 
                      variant="outlined" 
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { backgroundColor: 'action.hover' }
                      }}
                    >
                      <CardContent 
                        onClick={() => handleToggleArticle(index)}
                        sx={{ pb: expandedArticles.has(index) ? 1 : 2 }}
                      >
                        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                          <Box sx={{ flexGrow: 1, mr: 2 }}>
                            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                              {article.title}
                            </Typography>
                            <Box display="flex" gap={1} mb={1} flexWrap="wrap">
                              <Chip label={article.symbol} size="small" color="primary" />
                              <Chip label={article.type} size="small" variant="outlined" />
                              <Chip 
                                label={getSentimentLabel(article.sentiment)} 
                                size="small" 
                                color={getSentimentColor(article.sentiment)}
                                variant="filled"
                              />
                              {article.published_date && (
                                <Chip label={formatDate(article.published_date)} size="small" variant="outlined" />
                              )}
                            </Box>
                            {!expandedArticles.has(index) && article.summary && (
                              <Typography variant="body2" color="textSecondary">
                                {article.summary}
                              </Typography>
                            )}
                          </Box>
                          <Box>
                            {expandedArticles.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </Box>
                        </Box>
                        
                        <Collapse in={expandedArticles.has(index)}>
                          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, mb: 2 }}>
                              {article.content || article.summary || 'No content available'}
                            </Typography>
                            
                            {/* Summarize Button */}
                            <Box sx={{ mb: 2 }}>
                              <Button
                                variant="outlined"
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSummarizeArticle(article, index);
                                }}
                                disabled={summarizingArticles.has(index)}
                                sx={{ mr: 1 }}
                              >
                                {summarizingArticles.has(index) ? (
                                  <>
                                    <CircularProgress size={16} sx={{ mr: 1 }} />
                                    Summarizing...
                                  </>
                                ) : (
                                  summaries.has(index) ? 'Update Summary' : 'Summarize'
                                )}
                              </Button>
                            </Box>
                            
                            {/* Summary Display */}
                            {summaries.has(index) && (
                              <Box sx={{ 
                                mt: 2, 
                                p: 2, 
                                backgroundColor: 'background.default', 
                                borderRadius: 1, 
                                border: '1px solid', 
                                borderColor: 'divider' 
                              }}>
                                <Typography variant="subtitle2" fontWeight="bold" gutterBottom color="primary">
                                  AI Summary - Portfolio Impact Analysis
                                </Typography>
                                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                                  {summaries.get(index)}
                                </Typography>
                              </Box>
                            )}
                            
                            {article.source && (
                              <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
                                Source: {article.source}
                              </Typography>
                            )}
                          </Box>
                        </Collapse>
                      </CardContent>
                    </Card>
                  </Box>
                ))}
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
      <Modal
        open={emailModalOpen}
        onClose={handleEmailModalClose}
      >
        <Box sx={modalStyle}>
          <Typography variant="h6">Draft Email</Typography>
          <TextField fullWidth label="Subject" value={email.subject} sx={{ mt: 2 }} />
          <TextField fullWidth multiline rows={10} label="Body" value={email.body} sx={{ mt: 2 }} />
          <Button onClick={handleEmailModalClose} sx={{ mt: 2 }}>Close</Button>
        </Box>
      </Modal>

      <Modal
        open={articleModalOpen}
        onClose={handleArticleClose}
      >
        <Box sx={modalStyle}>
          <Typography variant="h6">Article/Report Content</Typography>
          <Typography sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>{articleContent}</Typography>
          <Button onClick={handleArticleClose} sx={{ mt: 2 }}>Close</Button>
        </Box>
      </Modal>
    </Grid>
  );
};

export default AccountDrilldown;
