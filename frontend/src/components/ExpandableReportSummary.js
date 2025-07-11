import React, { useState } from 'react';
import { Typography, Button, Collapse, Box } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AssessmentIcon from '@mui/icons-material/Assessment';

const ExpandableReportSummary = ({ report, onReadFullReport }) => {
  const [expanded, setExpanded] = useState(false);

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  const handleReadFullReport = () => {
    if (onReadFullReport && report.document_id) {
      onReadFullReport(report.document_id, report.index || 'financial_reports');
    }
  };

  return (
    <div style={{ marginBottom: '16px', borderLeft: '3px solid #4caf50', paddingLeft: '12px' }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
        {report.title}
      </Typography>
      
      {report.symbol && (
        <Typography variant="caption" color="primary">
          {report.symbol}
        </Typography>
      )}
      
      {report.published_date && (
        <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
          • {new Date(report.published_date).toLocaleDateString()}
        </Typography>
      )}

      <Typography variant="body2" sx={{ mt: 0.5 }}>
        {report.summary}
      </Typography>

      {report.summary_full && report.summary_full !== report.summary && (
        <>
          <Collapse in={expanded}>
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Full Summary:
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ mt: 0.5 }}
                dangerouslySetInnerHTML={{ __html: report.summary_full }}
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

      {report.document_id && (
        <Button
          size="small"
          onClick={handleReadFullReport}
          startIcon={<AssessmentIcon />}
          variant="outlined"
          sx={{ mt: 1 }}
        >
          Read Full Report
        </Button>
      )}
    </div>
  );
};

export default ExpandableReportSummary;