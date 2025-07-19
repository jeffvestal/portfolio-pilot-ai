import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  IconButton,
  Typography,
  Snackbar,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CloseIcon from '@mui/icons-material/Close';
import EmailIcon from '@mui/icons-material/Email';

const EmailDraftPopup = ({ open, onClose, emailData, loading, error }) => {
  const [copySuccess, setCopySuccess] = useState('');
  const [openSnackbar, setOpenSnackbar] = useState(false);

  const handleCopy = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(`${type} copied to clipboard!`);
      setOpenSnackbar(true);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setCopySuccess('Failed to copy to clipboard');
      setOpenSnackbar(true);
    }
  };

  const handleCopyAll = async () => {
    if (!emailData) return;
    
    const fullEmail = `Subject: ${emailData.subject}\n\n${emailData.body}`;
    try {
      await navigator.clipboard.writeText(fullEmail);
      setCopySuccess('Complete email copied to clipboard!');
      setOpenSnackbar(true);
    } catch (err) {
      console.error('Failed to copy email: ', err);
      setCopySuccess('Failed to copy to clipboard');
      setOpenSnackbar(true);
    }
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
    setCopySuccess('');
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            minHeight: '500px',
            maxHeight: '80vh'
          }
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            pb: 1
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EmailIcon color="primary" />
            <Typography variant="h6">Draft Client Email</Typography>
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: 'text.secondary' }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <Divider />

        <DialogContent sx={{ pt: 2 }}>
          {loading && (
            <Box 
              display="flex" 
              flexDirection="column" 
              alignItems="center" 
              justifyContent="center"
              py={4}
            >
              <CircularProgress size={40} sx={{ mb: 2 }} />
              <Typography variant="body2" color="textSecondary">
                Generating personalized email based on market analysis...
              </Typography>
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {typeof error === 'string' ? error : 'An error occurred while generating the email'}
            </Alert>
          )}

          {emailData && !loading && (
            <Box>
              {/* Subject Field */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Subject
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={() => handleCopy(emailData.subject, 'Subject')}
                    sx={{ ml: 1 }}
                    title="Copy subject"
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Box>
                <TextField
                  fullWidth
                  variant="outlined"
                  value={emailData.subject}
                  InputProps={{
                    readOnly: true,
                  }}
                  sx={{
                    '& .MuiInputBase-input': {
                      backgroundColor: 'background.paper',
                      fontWeight: 'medium'
                    }
                  }}
                />
              </Box>

              {/* Body Field */}
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Email Body
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={() => handleCopy(emailData.body, 'Email body')}
                    sx={{ ml: 1 }}
                    title="Copy email body"
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Box>
                <TextField
                  fullWidth
                  multiline
                  rows={12}
                  variant="outlined"
                  value={emailData.body}
                  InputProps={{
                    readOnly: true,
                  }}
                  sx={{
                    '& .MuiInputBase-input': {
                      backgroundColor: 'background.paper',
                      fontFamily: 'monospace',
                      fontSize: '0.9rem',
                      lineHeight: 1.5
                    }
                  }}
                />
              </Box>

              {/* Usage Note */}
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  This email has been generated based on your client's current holdings and recent market developments. 
                  Please review and customize as needed before sending.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={onClose} color="secondary">
            Close
          </Button>
          {emailData && !loading && (
            <Button
              onClick={handleCopyAll}
              variant="contained"
              startIcon={<ContentCopyIcon />}
              color="primary"
            >
              Copy Complete Email
            </Button>
          )}
        </DialogActions>
      </Dialog>

      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity="success" 
          sx={{ width: '100%' }}
        >
          {copySuccess}
        </Alert>
      </Snackbar>
    </>
  );
};

export default EmailDraftPopup;