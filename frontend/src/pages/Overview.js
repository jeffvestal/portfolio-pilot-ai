import React, { useState, useEffect } from 'react';
import { Button, Card, CardContent, Grid, Typography, CircularProgress, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ExpandableNewsSummary from '../components/ExpandableNewsSummary';
import ExpandableReportSummary from '../components/ExpandableReportSummary';
import FullArticleDialog from '../components/FullArticleDialog';
import FullReportDialog from '../components/FullReportDialog';

const Overview = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [articleDialogOpen, setArticleDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState({ documentId: null, index: null });
  const [selectedReport, setSelectedReport] = useState({ documentId: null, index: null });

  const fetchMetrics = async () => {
    const response = await axios.get('http://localhost:8000/metrics/overview');
    setMetrics(response.data);
  };

  const fetchMetricsWithContent = async () => {
    setNewsLoading(true);
    setReportsLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/metrics/overview?include_news=true&include_reports=true');
      setMetrics(response.data);
    } finally {
      setNewsLoading(false);
      setReportsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics(); // Initial load without news
  }, []);

  const handleStartDay = async () => {
    setLoading(true);
    await axios.post('http://localhost:8000/agent/start_day');
    fetchMetricsWithContent(); // Load with news and reports after "Start Day"
    setLoading(false);
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
                <Typography variant="h6">Impact Summary</Typography>
                <Typography>{metrics.impact_summary}</Typography>
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
