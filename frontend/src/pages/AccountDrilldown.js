import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, CardContent, Grid, Typography, Modal, Box, TextField, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 600,
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  maxHeight: '80vh',
  overflowY: 'auto',
};

const AccountDrilldown = () => {
  const { accountId } = useParams();
  const [account, setAccount] = useState(null);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [email, setEmail] = useState({ subject: '', body: '' });
  const [articleModalOpen, setArticleModalOpen] = useState(false);
  const [articleContent, setArticleContent] = useState('');

  useEffect(() => {
    const fetchAccount = async () => {
      const response = await axios.get(`http://localhost:8000/account/${accountId}`);
      setAccount(response.data);
    };
    fetchAccount();
  }, [accountId]);

  const handleEmailModalOpen = async (articleId) => {
    const response = await axios.post('http://localhost:8000/email/draft', { 
      account_id: accountId,
      article_id: articleId 
    });
    setEmail(response.data);
    setEmailModalOpen(true);
  };

  const handleEmailModalClose = () => setEmailModalOpen(false);

  const handleArticleOpen = async (articleId, type) => {
    try {
      const endpoint = type === 'news' ? `/article/${articleId}` : `/report/${articleId}`;
      const response = await axios.get(`http://localhost:8000${endpoint}`);
      setArticleContent(response.data.content);
      setArticleModalOpen(true);
    } catch (error) {
      console.error("Error fetching article/report content:", error);
      setArticleContent("Could not load content.");
      setArticleModalOpen(true);
    }
  };

  const handleArticleClose = () => {
    setArticleModalOpen(false);
    setArticleContent('');
  };

  if (!account) return <div>Loading...</div>;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4">{account.account_name}</Typography>
        <Typography variant="subtitle1">{account.state} - {account.type} - {account.risk_profile}</Typography>
      </Grid>
      <Grid item xs={12}>
        <Button variant="contained" onClick={() => handleEmailModalOpen(account.relevant_news.articles[0].id)}>Draft Email</Button>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6">Holdings</Typography>
            {account.holdings.map((holding, index) => (
              <div key={index}>
                <Typography>{holding.company_name} ({holding.symbol}): {holding.total_quantity} shares, Total Value: ${holding.total_current_value.toLocaleString()}</Typography>
                <Typography variant="body2" color="textSecondary">Sector: {holding.sector}</Typography>
              </div>
            ))}
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6">Relevant News</Typography>
            <Typography>{account.relevant_news.summary}</Typography>
            <List>
              {account.relevant_news.articles.map((article, index) => (
                <ListItem button key={index} onClick={() => handleArticleOpen(article.id, 'news')}>
                  <ListItemText primary={article.title} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
      <Modal
        open={emailModalOpen}
        onClose={handleEmailModalClose}
      >
        <Box sx={modalStyle}>
          <Typography variant="h6">Draft Email</Typography>
          <TextField fullWidth label="Subject" value={email.subject} sx={{ mt: 2 }} />
          <TextField fullWidth multiline rows={10} label="Body" value={email.body} sx={{ mt: 2 }} />
          <Button onClick={handleEmailModalClose} sx={{ mt: 2 }}>Close</Button>
        </Box>
      </Modal>

      <Modal
        open={articleModalOpen}
        onClose={handleArticleClose}
      >
        <Box sx={modalStyle}>
          <Typography variant="h6">Article/Report Content</Typography>
          <Typography sx={{ mt: 2, whiteSpace: 'pre-wrap' }}>{articleContent}</Typography>
          <Button onClick={handleArticleClose} sx={{ mt: 2 }}>Close</Button>
        </Box>
      </Modal>
    </Grid>
  );
};

export default AccountDrilldown;
