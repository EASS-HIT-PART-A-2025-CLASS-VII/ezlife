import React, { useState, useEffect } from 'react';
import { FaFile, FaFileImage, FaFilePdf, FaFileAlt, FaTrash, FaDownload } from 'react-icons/fa';
import api from '../utils/api';
import './FilesPage.css';

function FilesPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');  // Fetch user's files on component mount
  useEffect(() => {
    console.log('FilesPage mounted, fetching files...');
    fetchFiles();
  }, []);
  const fetchFiles = async () => {
    setLoading(true);
    try {
      // Get user ID from local storage (token is the email address in this implementation)
      const authToken = localStorage.getItem('authToken');
      console.log('Auth token:', authToken ? `${authToken}` : 'null'); // Log full token for debugging
      
      if (!authToken) {
        setError('You must be logged in to view files');
        return;
      }

      // In this implementation, the token is simply the user's email address
      const userId = authToken;
      console.log('Making API request to:', `/files/${userId}`);

      const response = await api.get(`/files/${userId}`);
      console.log('Files API response:', response.data);
      setFiles(response.data);
      
      if (response.data.length === 0) {
        setSuccessMessage('You have no files yet. Upload your first file above!');
      }
    } catch (error) {
      console.error('Error fetching files:', error);
      setError('Failed to load files: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      const fileExt = file.name.split('.').pop().toLowerCase();
      if (!['jpg', 'jpeg', 'png', 'pdf', 'txt'].includes(fileExt)) {
        setError('Invalid file type. Only JPG, PNG, PDF, and TXT files are allowed.');
        return;
      }
      
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File size exceeds 5MB limit.');
        return;
      }
      
      setSelectedFile(file);
      setError('');
    }
  };
  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }
    
    setUploading(true);
    setError('');
    setSuccessMessage('');
    try {
      // Get user ID from token (which is the email address in this implementation)
      const authToken = localStorage.getItem('authToken');
      console.log('Uploading file for user token:', authToken);
      
      if (!authToken) {
        setError('You must be logged in to upload files');
        return;
      }
      
      const userId = authToken;
      
      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('description', description);
      formData.append('user_id', userId);
      
      console.log('Uploading file:', selectedFile.name, 'for user:', userId);
      
      // Upload file
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('Upload response:', response.data);
      
      // Update files list with the new file
      setFiles([...files, response.data]);
      setSuccessMessage('File uploaded successfully!');
      
      // Reset form
      setSelectedFile(null);
      setDescription('');
      document.getElementById('file-input').value = '';
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.response?.data?.detail || 'Failed to upload file: ' + (error.message || 'Unknown error'));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        await api.delete(`/files/${fileId}`);
        setFiles(files.filter(file => file._id !== fileId));
        setSuccessMessage('File deleted successfully!');
      } catch (error) {
        console.error('Error deleting file:', error);
        setError('Failed to delete file');
      }
    }
  };  const handleDownload = async (fileId, fileName) => {
    try {
      console.log('Downloading file:', fileName, 'with ID:', fileId);
      // Use the fileBaseURL from the API configuration
      const downloadUrl = `http://localhost:8003/files/download/${fileId}`;
      console.log('Download URL:', downloadUrl);
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      setError('Failed to download file: ' + (error.message || 'Unknown error'));
    }
  };

  const getFileIcon = (fileType) => {
    switch(fileType) {
      case 'jpg':
      case 'jpeg':
      case 'png':
        return <FaFileImage className="file-icon image-icon" />;
      case 'pdf':
        return <FaFilePdf className="file-icon pdf-icon" />;
      case 'txt':
        return <FaFileAlt className="file-icon text-icon" />;
      default:
        return <FaFile className="file-icon" />;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="page-container">
      <div className="files-page-content">
        <h1 className="page-title">My Files</h1>
        <p className="page-subtitle">Upload, manage, and download your files</p>

        {/* Upload Section */}
        <div className="content-card">
          <div className="content-card-header">
            <h2 className="card-title">Upload New File</h2>
          </div>
          
          <form onSubmit={handleUpload} className="upload-form">
            <div className="form-group">
              <label htmlFor="file-input">Select File (JPG, PNG, PDF, TXT - Max 5MB)</label>
              <input
                type="file"
                id="file-input"
                onChange={handleFileChange}
                accept=".jpg,.jpeg,.png,.pdf,.txt"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="description">Description (Optional)</label>
              <input
                type="text"
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter file description"
              />
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={uploading || !selectedFile}
            >
              {uploading ? 'Uploading...' : 'Upload File'}
            </button>
          </form>

          {error && <div className="error-message">{error}</div>}
          {successMessage && <div className="success-message">{successMessage}</div>}
        </div>

        {/* Files List */}
        <div className="content-card">
          <div className="content-card-header">
            <h2 className="card-title">Your Files</h2>
          </div>

          {loading ? (
            <div className="loading-indicator">Loading files...</div>
          ) : files.length === 0 ? (
            <div className="no-files-message">
              <p>You haven't uploaded any files yet.</p>
            </div>
          ) : (
            <div className="files-table-container">
              <table className="files-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Filename</th>
                    <th>Description</th>
                    <th>Size</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map(file => (
                    <tr key={file._id}>
                      <td className="file-type-cell">
                        {getFileIcon(file.file_type)}
                      </td>
                      <td>{file.original_filename}</td>
                      <td>{file.description || '-'}</td>
                      <td>{formatFileSize(file.file_size)}</td>
                      <td>{formatDate(file.upload_time)}</td>
                      <td className="actions-cell">
                        <button
                          className="btn-icon btn-download"
                          onClick={() => handleDownload(file._id, file.original_filename)}
                          title="Download"
                        >
                          <FaDownload />
                        </button>
                        <button
                          className="btn-icon btn-delete"
                          onClick={() => handleDelete(file._id)}
                          title="Delete"
                        >
                          <FaTrash />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default FilesPage;
