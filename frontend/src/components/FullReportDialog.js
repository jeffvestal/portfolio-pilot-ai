import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Box,
  Chip,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import AssessmentIcon from '@mui/icons-material/Assessment';
import axios from 'axios';

const FullReportDialog = ({ open, onClose, documentId, index }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (open && documentId) {
      fetchFullReport();
    }
  }, [open, documentId, index]);

  const fetchFullReport = async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const response = await axios.get(
        `http://localhost:8000/article/full/${documentId}?index=${index || 'financial_reports'}`
      );
      setReport(response.data);
    } catch (err) {
      console.error('Error fetching full report:', err);
      setError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setReport(null);
    setError(null);
    onClose();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        style: { minHeight: '500px' }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            <AssessmentIcon sx={{ mr: 1, color: '#4caf50' }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              {loading ? 'Loading Report...' : (report?.title || 'Full Report')}
            </Typography>
          </Box>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {report && (
          <Box>
            {/* Report metadata */}
            <Box sx={{ mb: 3, pb: 2, borderBottom: '1px solid #e0e0e0' }}>
              {report.published_date && (
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Published: {formatDate(report.published_date)}
                </Typography>
              )}
              
              <Box display="flex" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>
                <Chip 
                  icon={<AssessmentIcon />} 
                  label="Financial Report" 
                  size="small" 
                  color="success" 
                />
                {report.symbol && (
                  <Chip label={report.symbol} size="small" color="primary" />
                )}
                {report.source && (
                  <Chip label={report.source} size="small" variant="outlined" />
                )}
                {report.index && (
                  <Chip label={report.index} size="small" variant="outlined" />
                )}
              </Box>
            </Box>

            {/* Report content */}
            <Typography 
              variant="body1" 
              sx={{ 
                lineHeight: 1.7,
                '& em': {
                  fontStyle: 'italic',
                  backgroundColor: '#e8f5e8',
                  padding: '0 2px'
                }
              }}
              dangerouslySetInnerHTML={{ __html: report.content }}
            />

            {/* External link if available */}
            {report.url && (
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                <Button
                  variant="outlined"
                  startIcon={<OpenInNewIcon />}
                  href={report.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View Original Report
                </Button>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {report?.url && (
          <Button
            variant="contained"
            startIcon={<OpenInNewIcon />}
            href={report.url}
            target="_blank"
            rel="noopener noreferrer"
            color="success"
          >
            Open in New Tab
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default FullReportDialog;