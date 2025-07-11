import React, { useState } from 'react';
import { Typography, Button, Collapse, Box } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ArticleIcon from '@mui/icons-material/Article';

const ExpandableNewsSummary = ({ story, onReadFullArticle }) => {
  const [expanded, setExpanded] = useState(false);

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  const handleReadFullArticle = () => {
    if (onReadFullArticle && story.document_id) {
      onReadFullArticle(story.document_id, story.index || 'financial_news');
    }
  };

  return (
    <div style={{ marginBottom: '16px', borderLeft: '3px solid #1976d2', paddingLeft: '12px' }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
        {story.title}
      </Typography>
      
      {story.symbol && (
        <Typography variant="caption" color="primary">
          {story.symbol}
        </Typography>
      )}
      
      {story.published_date && (
        <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
          • {new Date(story.published_date).toLocaleDateString()}
        </Typography>
      )}

      <Typography variant="body2" sx={{ mt: 0.5 }}>
        {story.summary}
      </Typography>

      {story.summary_full && story.summary_full !== story.summary && (
        <>
          <Collapse in={expanded}>
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Full Summary:
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ mt: 0.5 }}
                dangerouslySetInnerHTML={{ __html: story.summary_full }}
              />
            </Box>
          </Collapse>
          
          <Button
            size="small"
            onClick={handleToggle}
            startIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{ mt: 1, mr: 1 }}
          >
            {expanded ? 'Show Less' : 'Show More'}
          </Button>
        </>
      )}

      {story.document_id && (
        <Button
          size="small"
          onClick={handleReadFullArticle}
          startIcon={<ArticleIcon />}
          variant="outlined"
          sx={{ mt: 1 }}
        >
          Read Full Article
        </Button>
      )}
    </div>
  );
};

export default ExpandableNewsSummary;