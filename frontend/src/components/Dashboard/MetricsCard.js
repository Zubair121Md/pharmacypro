import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Box, 
  Typography, 
  Avatar, 
  IconButton, 
  TextField, 
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import { Edit as EditIcon, Save as SaveIcon, Cancel as CancelIcon, Info as InfoIcon } from '@mui/icons-material';
import Tooltip from '@mui/material/Tooltip';

function MetricsCard({ 
  title, 
  value, 
  icon, 
  color = 'primary', 
  format = 'number', 
  editable = false, 
  onSave = null,
  onCancel = null,
  tooltip = ''
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [openDialog, setOpenDialog] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const formatValue = (val) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2,
      }).format(val);
    }
    if (format === 'percentage') {
      return `${val}%`;
    }
    return val.toLocaleString();
  };

  const handleEdit = () => {
    setEditValue(value);
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (onSave) {
      setSaving(true);
      setError(null);
      try {
        await onSave(editValue);
        setIsEditing(false);
        setOpenDialog(false);
      } catch (err) {
        setError(err.message || 'Failed to save changes');
      } finally {
        setSaving(false);
      }
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
    setOpenDialog(false);
    setError(null);
    if (onCancel) {
      onCancel();
    }
  };

  const handleEditClick = () => {
    if (editable) {
      setOpenDialog(true);
    }
  };

  return (
    <>
      <Card sx={{ cursor: editable ? 'pointer' : 'default' }} onClick={handleEditClick}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography color="textSecondary" gutterBottom variant="h6">
                  {title}
                </Typography>
            {tooltip && (
              <Tooltip title={tooltip} arrow>
                <InfoIcon fontSize="small" color="action" />
              </Tooltip>
            )}
                {editable && (
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleEdit(); }}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
              <Typography variant="h4">
                {formatValue(value)}
              </Typography>
            </Box>
            <Avatar
              sx={{
                backgroundColor: `${color}.main`,
                height: 56,
                width: 56,
              }}
            >
              {icon}
            </Avatar>
          </Box>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCancel} maxWidth="sm" fullWidth>
        <DialogTitle>
          Edit {title}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            label={title}
            type={format === 'currency' ? 'number' : 'text'}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            variant="outlined"
            sx={{ mt: 2 }}
            helperText={format === 'currency' ? 'Enter amount in rupees' : 'Enter new value'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel} disabled={saving}>
            Cancel
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            startIcon={<SaveIcon />}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Permanently'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default MetricsCard;
