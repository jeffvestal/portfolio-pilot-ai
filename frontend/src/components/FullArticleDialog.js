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
import axios from 'axios';

const FullArticleDialog = ({ open, onClose, documentId, index }) => {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (open && documentId) {
      fetchFullArticle();
    }
  }, [open, documentId, index]);

  const fetchFullArticle = async () => {
    setLoading(true);
    setError(null);
    setArticle(null);

    try {
      const response = await axios.get(
        `http://localhost:8000/article/full/${documentId}?index=${index || 'financial_news'}`
      );
      setArticle(response.data);
    } catch (err) {
      console.error('Error fetching full article:', err);
      setError(err.response?.data?.detail || 'Failed to load article');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setArticle(null);
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
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {loading ? 'Loading Article...' : (article?.title || 'Full Article')}
          </Typography>
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

        {article && (
          <Box>
            {/* Article metadata */}
            <Box sx={{ mb: 3, pb: 2, borderBottom: '1px solid #e0e0e0' }}>
              {article.published_date && (
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Published: {formatDate(article.published_date)}
                </Typography>
              )}
              
              <Box display="flex" gap={1} flexWrap="wrap" sx={{ mt: 1 }}>
                {article.symbol && (
                  <Chip label={article.symbol} size="small" color="primary" />
                )}
                {article.source && (
                  <Chip label={article.source} size="small" variant="outlined" />
                )}
                {article.index && (
                  <Chip label={article.index} size="small" variant="outlined" />
                )}
              </Box>
            </Box>

            {/* Article content */}
            <Typography 
              variant="body1" 
              sx={{ 
                lineHeight: 1.7,
                '& em': {
                  fontStyle: 'italic',
                  backgroundColor: '#fff3cd',
                  padding: '0 2px'
                }
              }}
              dangerouslySetInnerHTML={{ __html: article.content }}
            />

            {/* External link if available */}
            {article.url && (
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                <Button
                  variant="outlined"
                  startIcon={<OpenInNewIcon />}
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View Original Article
                </Button>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        {article?.url && (
          <Button
            variant="contained"
            startIcon={<OpenInNewIcon />}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open in New Tab
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default FullArticleDialog;