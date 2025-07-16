import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  TextField,
  Typography
} from '@mui/material';

const TimePeriodSelector = ({ 
  timePeriod, 
  timeUnit, 
  onTimePeriodChange, 
  onTimeUnitChange,
  disabled = false 
}) => {
  const timeUnits = [
    { value: 'minutes', label: 'Minutes' },
    { value: 'hours', label: 'Hours' },
    { value: 'days', label: 'Days' }
  ];

  const getPresetOptions = () => {
    switch (timeUnit) {
      case 'minutes':
        return [
          { value: 15, label: '15 minutes' },
          { value: 30, label: '30 minutes' },
          { value: 60, label: '1 hour' },
          { value: 120, label: '2 hours' }
        ];
      case 'hours':
        return [
          { value: 1, label: '1 hour' },
          { value: 6, label: '6 hours' },
          { value: 12, label: '12 hours' },
          { value: 24, label: '24 hours' },
          { value: 48, label: '48 hours' }
        ];
      case 'days':
        return [
          { value: 1, label: '1 day' },
          { value: 3, label: '3 days' },
          { value: 7, label: '1 week' },
          { value: 14, label: '2 weeks' },
          { value: 30, label: '1 month' }
        ];
      default:
        return [];
    }
  };

  const presetOptions = getPresetOptions();
  const isPresetValue = presetOptions.some(option => option.value === timePeriod);

  return (
    <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
      <Typography variant="body2" color="textSecondary" sx={{ minWidth: 'fit-content' }}>
        Time Period:
      </Typography>
      
      <TextField
        label="Period"
        type="number"
        value={timePeriod}
        onChange={(e) => onTimePeriodChange(parseInt(e.target.value) || 1)}
        inputProps={{ min: 1, max: timeUnit === 'minutes' ? 1440 : timeUnit === 'hours' ? 168 : 365 }}
        size="small"
        sx={{ width: 100 }}
        disabled={disabled}
      />

      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>Unit</InputLabel>
        <Select
          value={timeUnit}
          label="Unit"
          onChange={(e) => onTimeUnitChange(e.target.value)}
          disabled={disabled}
        >
          {timeUnits.map((unit) => (
            <MenuItem key={unit.value} value={unit.value}>
              {unit.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {presetOptions.length > 0 && (
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Quick Select</InputLabel>
          <Select
            value={isPresetValue ? timePeriod : ''}
            label="Quick Select"
            onChange={(e) => onTimePeriodChange(e.target.value)}
            disabled={disabled}
          >
            <MenuItem value="">
              <em>Custom</em>
            </MenuItem>
            {presetOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </Box>
  );
};

export default TimePeriodSelector;