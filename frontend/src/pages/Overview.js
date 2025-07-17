import React, { useState, useEffect } from 'react';
import { Button, Card, CardContent, Grid, Typography, CircularProgress, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useMCPNotification } from '../contexts/MCPNotificationContext';
import axios from 'axios';
import ExpandableNewsSummary from '../components/ExpandableNewsSummary';
import ExpandableReportSummary from '../components/ExpandableReportSummary';
import FullArticleDialog from '../components/FullArticleDialog';
import FullReportDialog from '../components/FullReportDialog';

const Overview = () => {
  const navigate = useNavigate();
  const { showMCPTool, hideMCPTool } = useMCPNotification();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [actionItemLoading, setActionItemLoading] = useState(false);
  const [actionItem, setActionItem] = useState(null);
  const [articleDialogOpen, setArticleDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState({ documentId: null, index: null });
  const [selectedReport, setSelectedReport] = useState({ documentId: null, index: null });

  const fetchMetrics = async () => {
    const response = await axios.get('http://localhost:8000/metrics/overview');
    setMetrics(response.data);
  };

  const fetchMetricsWithContent = async () => {
    const notificationId = showMCPTool('Enhanced Content Loading', 'Fetching AI-enhanced news and reports summaries');
    
    setNewsLoading(true);
    setReportsLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/metrics/overview?include_news=true&include_reports=true');
      setMetrics(response.data);
    } finally {
      setNewsLoading(false);
      setReportsLoading(false);
      hideMCPTool(notificationId);
    }
  };

  const fetchActionItem = async () => {
    const notificationId = showMCPTool('Analyzing Top Accounts for Negative News', 'Checking for negative news affecting your most valuable accounts');
    
    setActionItemLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/action-item');
      setActionItem(response.data);
    } catch (error) {
      console.error('Error fetching action item:', error);
      setActionItem({
        status: 'error',
        message: 'Error loading action item analysis',
        top_accounts: [],
        negative_news: []
      });
    } finally {
      setActionItemLoading(false);
      hideMCPTool(notificationId);
    }
  };

  useEffect(() => {
    fetchMetrics(); // Initial load without news
  }, []);

  const handleStartDay = async () => {
    const notificationId = showMCPTool('Start Day Analysis', 'Running daily portfolio analysis and content enhancement');
    
    setLoading(true);
    try {
      await axios.post('http://localhost:8000/agent/start_day');
      fetchMetricsWithContent(); // Load with news and reports after "Start Day"
      fetchActionItem(); // Load action item analysis
    } finally {
      setLoading(false);
      hideMCPTool(notificationId);
    }
  };

  const handleReadFullArticle = (documentId, index) => {
    setSelectedArticle({ documentId, index });
    setArticleDialogOpen(true);
  };

  const handleCloseArticleDialog = () => {
    setArticleDialogOpen(false);
    setSelectedArticle({ documentId: null, index: null });
  };

  const handleReadFullReport = (documentId, index) => {
    setSelectedReport({ documentId, index });
    setReportDialogOpen(true);
  };

  const handleCloseReportDialog = () => {
    setReportDialogOpen(false);
    setSelectedReport({ documentId: null, index: null });
  };

  const handleAccountClick = (accountId) => {
    navigate(`/account/${accountId}`);
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Button variant="contained" onClick={handleStartDay} disabled={loading}>
          {loading ? 'Processing...' : 'Start Day'}
        </Button>
      </Grid>
      {metrics && (
        <>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate('/accounts')}
            >
              <CardContent>
                <Typography variant="h5">{metrics.total_accounts}</Typography>
                <Typography color="textSecondary">Total Accounts</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h5">${metrics.total_aum.toLocaleString()}</Typography>
                <Typography color="textSecondary">Total AUM</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate('/news')}
            >
              <CardContent>
                <Typography variant="h5">{metrics.total_news}</Typography>
                <Typography color="textSecondary">Total News</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card 
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate('/reports')}
            >
              <CardContent>
                <Typography variant="h5">{metrics.total_reports}</Typography>
                <Typography color="textSecondary">Total Reports</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6">Action Item</Typography>
                
                {actionItemLoading && (
                  <Box display="flex" alignItems="center" sx={{ py: 2 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography color="textSecondary">
                      Analyzing top accounts for negative news...
                    </Typography>
                  </Box>
                )}
                
                {!actionItemLoading && !actionItem && (
                  <Typography color="textSecondary" sx={{ py: 2 }}>
                    Click "Start Day" to analyze your top accounts for negative news
                  </Typography>
                )}
                
                {!actionItemLoading && actionItem && (
                  <Box sx={{ py: 1 }}>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {actionItem.message}
                    </Typography>
                    
                    {actionItem.server_used && (
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Source: {actionItem.server_used}
                      </Typography>
                    )}
                    
                    {actionItem.status === 'success' && actionItem.affected_accounts && actionItem.affected_accounts.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>
                          Affected Accounts:
                        </Typography>
                        {actionItem.affected_accounts.map((account, index) => (
                          <Box key={index} sx={{ mb: 1 }}>
                            <Typography 
                              variant="body2" 
                              component="span"
                              sx={{ 
                                color: 'primary.main', 
                                cursor: 'pointer',
                                textDecoration: 'underline',
                                mr: 1
                              }}
                              onClick={() => handleAccountClick(account.account_id)}
                            >
                              {account.account_name}
                            </Typography>
                            <Typography variant="body2" component="span" color="textSecondary">
                              (${account.total_portfolio_value.toLocaleString()})
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                    
                    {actionItem.status === 'error' && (
                      <Typography color="error">
                        {actionItem.message}
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
          {/* News Summary - Left Column */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6">Latest News Summary</Typography>
                
                {newsLoading && (
                  <Box display="flex" alignItems="center" justifyContent="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography color="textSecondary">
                      Summarizing latest financial news...
                    </Typography>
                  </Box>
                )}
                
                {!newsLoading && metrics && metrics.news_summary === null && (
                  <Typography color="textSecondary" sx={{ py: 2 }}>
                    Click "Start Day" to summarize latest financial news
                  </Typography>
                )}
                
                {!newsLoading && metrics && metrics.news_summary && metrics.news_summary.status === 'success' && (
                  <>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      Source: {metrics.news_summary.server_used}
                    </Typography>
                    {metrics.news_summary.news_stories.map((story, index) => (
                      <ExpandableNewsSummary
                        key={index}
                        story={story}
                        onReadFullArticle={handleReadFullArticle}
                      />
                    ))}
                  </>
                )}
                
                {!newsLoading && metrics && metrics.news_summary && metrics.news_summary.status === 'no_servers' && (
                  <Typography color="textSecondary">
                    {metrics.news_summary.message}
                  </Typography>
                )}
                
                {!newsLoading && metrics && metrics.news_summary && metrics.news_summary.status === 'no_data' && (
                  <Typography color="warning.main">
                    {metrics.news_summary.message}
                  </Typography>
                )}
                
                {!newsLoading && metrics && metrics.news_summary && metrics.news_summary.status === 'error' && (
                  <Typography color="error">
                    {metrics.news_summary.message}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Reports Summary - Right Column */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6">Latest Reports Summary</Typography>
                
                {reportsLoading && (
                  <Box display="flex" alignItems="center" justifyContent="center" sx={{ py: 3 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography color="textSecondary">
                      Summarizing latest financial reports...
                    </Typography>
                  </Box>
                )}
                
                {!reportsLoading && metrics && metrics.reports_summary === null && (
                  <Typography color="textSecondary" sx={{ py: 2 }}>
                    Click "Start Day" to summarize latest financial reports
                  </Typography>
                )}
                
                {!reportsLoading && metrics && metrics.reports_summary && metrics.reports_summary.status === 'success' && (
                  <>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      Source: {metrics.reports_summary.server_used}
                    </Typography>
                    {metrics.reports_summary.reports.map((report, index) => (
                      <ExpandableReportSummary
                        key={index}
                        report={report}
                        onReadFullReport={handleReadFullReport}
                      />
                    ))}
                  </>
                )}
                
                {!reportsLoading && metrics && metrics.reports_summary && metrics.reports_summary.status === 'no_servers' && (
                  <Typography color="textSecondary">
                    {metrics.reports_summary.message}
                  </Typography>
                )}
                
                {!reportsLoading && metrics && metrics.reports_summary && metrics.reports_summary.status === 'no_data' && (
                  <Typography color="warning.main">
                    {metrics.reports_summary.message}
                  </Typography>
                )}
                
                {!reportsLoading && metrics && metrics.reports_summary && metrics.reports_summary.status === 'error' && (
                  <Typography color="error">
                    {metrics.reports_summary.message}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </>
      )}
      
      {/* Full Article Dialog */}
      <FullArticleDialog
        open={articleDialogOpen}
        onClose={handleCloseArticleDialog}
        documentId={selectedArticle.documentId}
        index={selectedArticle.index}
      />

      {/* Full Report Dialog */}
      <FullReportDialog
        open={reportDialogOpen}
        onClose={handleCloseReportDialog}
        documentId={selectedReport.documentId}
        index={selectedReport.index}
      />
    </Grid>
  );
};

export default Overview;
