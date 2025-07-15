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
import ArticleIcon from '@mui/icons-material/Article';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import FullArticleDialog from '../components/FullArticleDialog';
import axios from 'axios';

const NewsList = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [articleDialogOpen, setArticleDialogOpen] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState({ documentId: null, index: null });
  const itemsPerPage = 10;

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const response = await axios.get('http://localhost:8000/news');
      setNews(response.data.news);
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Failed to load news articles');
    } finally {
      setLoading(false);
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

  const filteredNews = React.useMemo(() => {
    return news.filter(article =>
      article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.source.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [news, searchTerm]);

  const paginatedNews = React.useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredNews.slice(startIndex, endIndex);
  }, [filteredNews, currentPage]);

  const totalPages = Math.ceil(filteredNews.length / itemsPerPage);

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
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <ArticleIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              Financial News
            </Typography>
          </Box>
          
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Total Articles: {news.length} | Showing: {filteredNews.length}
          </Typography>

          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search articles by title, symbol, content, or source..."
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
        {paginatedNews.map((article) => (
          <Grid item xs={12} key={article.id}>
            <Card sx={{ borderLeft: '3px solid #2196f3' }}>
              <CardContent>
                <Box display="flex" justifyContent="between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="h2" sx={{ flexGrow: 1, pr: 2 }}>
                    {article.title}
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {article.symbol && (
                      <Chip 
                        label={article.symbol} 
                        size="small" 
                        color="primary" 
                      />
                    )}
                    {article.source && (
                      <Chip 
                        label={article.source} 
                        size="small" 
                        variant="outlined" 
                      />
                    )}
                  </Box>
                </Box>

                {article.published_date && (
                  <Typography variant="caption" color="textSecondary" gutterBottom>
                    Published: {formatDate(article.published_date)}
                  </Typography>
                )}

                <Typography variant="body2" sx={{ mt: 1, mb: 2 }}>
                  {article.summary}
                </Typography>

                <Box display="flex" gap={1} flexWrap="wrap">
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<ArticleIcon />}
                    onClick={() => handleReadFullArticle(article.document_id, article.index)}
                  >
                    Read Full Article
                  </Button>
                  
                  {article.url && (
                    <Button
                      variant="text"
                      size="small"
                      startIcon={<OpenInNewIcon />}
                      href={article.url}
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

      {filteredNews.length === 0 && searchTerm && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Typography variant="body1" color="textSecondary">
            No news articles found matching "{searchTerm}"
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

      {/* Full Article Dialog */}
      <FullArticleDialog
        open={articleDialogOpen}
        onClose={handleCloseArticleDialog}
        documentId={selectedArticle.documentId}
        index={selectedArticle.index}
      />
    </div>
  );
};

export default NewsList;