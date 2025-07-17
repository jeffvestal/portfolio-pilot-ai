import React, { useState } from 'react';
import {
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Chip,
  Alert,
  Paper
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Build as BuildIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

const ChatMessageRenderer = ({ message }) => {
  const [expandedResults, setExpandedResults] = useState({});

  const handleAccordionChange = (resultId) => (event, isExpanded) => {
    setExpandedResults(prev => ({
      ...prev,
      [resultId]: isExpanded
    }));
  };

  // Parse tool results from message text
  const parseToolResults = (text) => {
    console.log('🔍 ChatMessageRenderer: Parsing message text:', text.substring(0, 200) + '...');
    const toolResultsRegex = /```json-tool-results\n([\s\S]*?)\n```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = toolResultsRegex.exec(text)) !== null) {
      console.log('🔍 Found tool results match:', match[1].substring(0, 100) + '...');
      // Add text before the tool results
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        });
      }

      // Parse and add tool results
      try {
        const toolResultsData = JSON.parse(match[1]);
        console.log('🔍 Successfully parsed tool results:', toolResultsData);
        parts.push({
          type: 'tool-results',
          data: toolResultsData
        });
      } catch (error) {
        console.error('❌ Error parsing tool results JSON:', error);
        console.error('❌ Raw JSON content:', match[1]);
        // Fallback to text if JSON parsing fails
        parts.push({
          type: 'text',
          content: match[0]
        });
      }

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after the last tool results
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }

    console.log('🔍 Final parsed parts:', parts.length, 'parts found');
    parts.forEach((part, index) => {
      console.log(`🔍 Part ${index}:`, part.type, part.type === 'tool-results' ? `- ${part.data?.tool_results?.length} tools` : '- text content');
    });
    return parts;
  };

  const renderToolResult = (toolResult, index) => {
    const isError = typeof toolResult.result === 'string' && 
                   (toolResult.result.includes('Error') || 
                    toolResult.result.includes('error') ||
                    toolResult.result.includes('illegal_argument_exception'));
    
    const resultText = typeof toolResult.result === 'object' 
      ? JSON.stringify(toolResult.result, null, 2)
      : String(toolResult.result);

    return (
      <Box key={index} sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {isError ? (
            <ErrorIcon color="error" sx={{ fontSize: 16 }} />
          ) : (
            <CheckCircleIcon color="success" sx={{ fontSize: 16 }} />
          )}
          <Chip 
            label={toolResult.tool_name} 
            size="small" 
            variant="outlined"
            sx={{ fontSize: '0.7rem' }}
          />
          {toolResult.timestamp && (
            <Typography variant="caption" color="textSecondary">
              {new Date(toolResult.timestamp * 1000).toLocaleTimeString()}
            </Typography>
          )}
        </Box>
        
        <Paper 
          variant="outlined" 
          sx={{ 
            p: 1, 
            bgcolor: isError ? 'rgba(211, 47, 47, 0.1)' : 'rgba(46, 125, 50, 0.1)',
            border: `1px solid ${isError ? 'error.main' : 'success.main'}`
          }}
        >
          <Typography 
            variant="body2" 
            component="pre"
            sx={{ 
              fontFamily: 'monospace',
              fontSize: '0.75rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              margin: 0,
              color: isError ? 'error.dark' : 'success.dark'
            }}
          >
            {resultText}
          </Typography>
        </Paper>
      </Box>
    );
  };

  const renderToolResults = (toolResultsData, index) => {
    console.log('🔍 Rendering tool results:', toolResultsData);
    const resultId = `tool-results-${index}`;
    const { turn, tool_results } = toolResultsData;
    const hasErrors = tool_results.some(tr => 
      typeof tr.result === 'string' && 
      (tr.result.includes('Error') || tr.result.includes('error') || tr.result.includes('illegal_argument_exception'))
    );
    console.log('🔍 Tool results component - Turn:', turn, 'Tools:', tool_results.length, 'Has errors:', hasErrors);

    return (
      <Box key={resultId} sx={{ my: 2 }}>
        <Accordion 
          expanded={expandedResults[resultId] || false}
          onChange={handleAccordionChange(resultId)}
          sx={{ 
            bgcolor: 'background.paper',
            '&:before': { display: 'none' },
            boxShadow: 1
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ 
              minHeight: 48,
              '& .MuiAccordionSummary-content': {
                alignItems: 'center',
                gap: 1
              }
            }}
          >
            <BuildIcon color="action" sx={{ fontSize: 20 }} />
            <Typography variant="body2" fontWeight="medium">
              Tool Results (Turn {turn})
            </Typography>
            <Chip 
              label={`${tool_results.length} tool${tool_results.length !== 1 ? 's' : ''}`}
              size="small"
              color={hasErrors ? "error" : "primary"}
              sx={{ fontSize: '0.7rem' }}
            />
            {hasErrors && (
              <Chip 
                label="Errors"
                size="small"
                color="error"
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            )}
          </AccordionSummary>
          <AccordionDetails sx={{ pt: 0 }}>
            <Box>
              {tool_results.map((toolResult, idx) => renderToolResult(toolResult, idx))}
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  const parts = parseToolResults(message);

  return (
    <Box>
      {parts.map((part, index) => {
        console.log('🔍 Rendering part:', index, part.type);
        if (part.type === 'tool-results') {
          console.log('🔍 Rendering tool-results component');
          return renderToolResults(part.data, index);
        } else {
          console.log('🔍 Rendering regular markdown content');
          // Render regular markdown content
          return (
            <Box key={index}>
              <ReactMarkdown>{part.content}</ReactMarkdown>
            </Box>
          );
        }
      })}
    </Box>
  );
};

export default ChatMessageRenderer;