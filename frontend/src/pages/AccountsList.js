import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  CircularProgress,
  Alert,
  TextField,
  Box,
  Chip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import axios from 'axios';

const AccountsList = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'total_portfolio_value', direction: 'desc' });
  const navigate = useNavigate();

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get('http://localhost:8000/accounts');
      setAccounts(response.data.accounts);
    } catch (err) {
      console.error('Error fetching accounts:', err);
      setError('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key) => {
    const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
  };

  const handleAccountClick = (accountId) => {
    navigate(`/account/${accountId}`);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value);
  };

  const filteredAndSortedAccounts = React.useMemo(() => {
    let filtered = accounts.filter(account =>
      account.account_holder_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.account_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.state.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (typeof aValue === 'string') {
          return sortConfig.direction === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        } else {
          return sortConfig.direction === 'asc' 
            ? aValue - bValue
            : bValue - aValue;
        }
      });
    }

    return filtered;
  }, [accounts, searchTerm, sortConfig]);

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
            <AccountBalanceIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              All Accounts
            </Typography>
          </Box>
          
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Total Accounts: {accounts.length}
          </Typography>

          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search accounts by name, ID, or state..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mt: 2 }}
          />
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel
                  active={sortConfig.key === 'account_id'}
                  direction={sortConfig.key === 'account_id' ? sortConfig.direction : 'asc'}
                  onClick={() => handleSort('account_id')}
                >
                  Account ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortConfig.key === 'account_holder_name'}
                  direction={sortConfig.key === 'account_holder_name' ? sortConfig.direction : 'asc'}
                  onClick={() => handleSort('account_holder_name')}
                >
                  Account Holder
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortConfig.key === 'state'}
                  direction={sortConfig.key === 'state' ? sortConfig.direction : 'asc'}
                  onClick={() => handleSort('state')}
                >
                  State
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortConfig.key === 'total_portfolio_value'}
                  direction={sortConfig.key === 'total_portfolio_value' ? sortConfig.direction : 'asc'}
                  onClick={() => handleSort('total_portfolio_value')}
                >
                  Portfolio Value
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAndSortedAccounts.map((account) => (
              <TableRow
                key={account.account_id}
                hover
                onClick={() => handleAccountClick(account.account_id)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {account.account_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {account.account_holder_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={account.state} 
                    size="small" 
                    variant="outlined" 
                    color="primary"
                  />
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight="medium" color="success.main">
                    {formatCurrency(account.total_portfolio_value)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredAndSortedAccounts.length === 0 && searchTerm && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Typography variant="body1" color="textSecondary">
            No accounts found matching "{searchTerm}"
          </Typography>
        </Box>
      )}
    </div>
  );
};

export default AccountsList;