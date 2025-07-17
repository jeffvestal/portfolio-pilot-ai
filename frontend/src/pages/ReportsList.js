import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  Box,
  Chip,
  Grid,
  Pagination,
  Button
} from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import FullReportDialog from '../components/FullReportDialog';
import axios from 'axios';

const ReportsList = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState({ documentId: null, index: null });
  const itemsPerPage = 10;

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    console.log('🔍 ReportsList: Starting to fetch reports...');
    try {
      const response = await axios.get('http://localhost:8000/reports');
      console.log('🔍 ReportsList: Raw response:', response);
      console.log('🔍 ReportsList: Response status:', response.status);
      console.log('🔍 ReportsList: Response data:', response.data);
      console.log('🔍 ReportsList: Reports array:', response.data.reports);
      console.log('🔍 ReportsList: Number of reports:', response.data.reports?.length);
      setReports(response.data.reports);
    } catch (err) {
      console.error('❌ ReportsList: Error fetching reports:', err);
      console.error('❌ ReportsList: Error response:', err.response?.data);
      console.error('❌ ReportsList: Error status:', err.response?.status);
      setError(`Failed to load financial reports: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReadFullReport = (documentId, index) => {
    setSelectedReport({ documentId, index });
    setReportDialogOpen(true);
  };

  const handleCloseReportDialog = () => {
    setReportDialogOpen(false);
    setSelectedReport({ documentId: null, index: null });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
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

  const filteredReports = React.useMemo(() => {
    return reports.filter(report =>
      (report.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (report.symbol || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (report.summary || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (report.source || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [reports, searchTerm]);

  const paginatedReports = React.useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredReports.slice(startIndex, endIndex);
  }, [filteredReports, currentPage]);

  const totalPages = Math.ceil(filteredReports.length / itemsPerPage);

  const handlePageChange = (event, value) => {
    setCurrentPage(value);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
          {process.env.NODE_ENV === 'development' && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Check browser console for detailed error information
            </Typography>
          )}
        </Alert>
        <Button 
          variant="outlined" 
          onClick={() => {
            setError(null);
            setLoading(true);
            fetchReports();
          }}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <AssessmentIcon sx={{ mr: 1, color: 'success.main' }} />
            <Typography variant="h4" component="h1">
              Financial Reports
            </Typography>
          </Box>
          
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Total Reports: {reports.length} | Showing: {filteredReports.length}
          </Typography>

          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search reports by title, symbol, content, or source..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1); // Reset to first page when searching
            }}
            sx={{ mt: 2 }}
          />
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {paginatedReports.map((report) => (
          <Grid item xs={12} key={report.id}>
            <Card sx={{ borderLeft: '3px solid #4caf50' }}>
              <CardContent>
                <Box display="flex" justifyContent="between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="h2" sx={{ flexGrow: 1, pr: 2 }}>
                    {report.title}
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {report.symbol && (
                      <Chip 
                        label={report.symbol} 
                        size="small" 
                        color="primary" 
                      />
                    )}
                    {report.source && (
                      <Chip 
                        label={report.source} 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                  </Box>
                </Box>

                {report.published_date && (
                  <Typography variant="caption" color="textSecondary" gutterBottom>
                    Published: {formatDate(report.published_date)}
                  </Typography>
                )}

                <Typography variant="body2" sx={{ mt: 1, mb: 2 }}>
                  {report.summary}
                </Typography>

                <Box display="flex" gap={1} flexWrap="wrap">
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AssessmentIcon />}
                    onClick={() => handleReadFullReport(report.document_id, report.index)}
                    color="success"
                  >
                    Read Full Report
                  </Button>
                  
                  {report.url && (
                    <Button
                      variant="text"
                      size="small"
                      startIcon={<OpenInNewIcon />}
                      href={report.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open Source
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredReports.length === 0 && searchTerm && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Typography variant="body1" color="textSecondary">
            No financial reports found matching "{searchTerm}"
          </Typography>
        </Box>
      )}

      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        </Box>
      )}

      {/* Full Report Dialog */}
      <FullReportDialog
        open={reportDialogOpen}
        onClose={handleCloseReportDialog}
        documentId={selectedReport.documentId}
        index={selectedReport.index}
      />
    </div>
  );
};

export default ReportsList;