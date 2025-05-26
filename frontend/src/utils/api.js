import axios from "axios";

// Create two separate API instances for different services
const authApi = axios.create({
  baseURL: "http://localhost:8001", // User-service for auth on port 8001
});

const taskApi = axios.create({
  baseURL: "http://localhost:8000", // Main backend for tasks on port 8000
});

// Add auth token to API requests if available
const addAuthInterceptor = (axiosInstance) => {
  axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      console.log(`Adding auth token to request: Bearer ${token.substring(0, 10)}...`);
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.log('No auth token found for request');
    }
    return config;
  }, (error) => {
    console.error("Request interceptor error:", error);
    return Promise.reject(error);
  });
  
  // Add response interceptor for better error handling
  axiosInstance.interceptors.response.use(
    response => response,
    error => {
      // Add more context to the error
      if (error.response) {
        console.error(`API Error (${error.response.status}):`, error.response.data);
        error.statusCode = error.response.status;
        error.responseData = error.response.data;
      } else if (error.request) {
        console.error('API Error: No response received', error.request);
        error.networkError = true;
      } else {
        console.error('API Error:', error.message);
      }
      
      // Re-throw the enhanced error
      return Promise.reject(error);
    }
  );
}

// Apply interceptor to both instances
addAuthInterceptor(taskApi);
addAuthInterceptor(authApi);

// Helper function to handle API errors
const handleApiError = (error) => {
  if (error.statusCode === 401) {
    // Unauthorized - clear token and redirect to login
    localStorage.removeItem('authToken');
    window.location.href = '/login';
    return Promise.reject(new Error('Session expired. Please login again.'));
  }
  
  return Promise.reject(error);
};

// Combined API object with methods that route to the appropriate service
const api = {
  // Auth methods go to the auth service
  post: (url, data, config) => {
    if (url === '/token') {
      console.log('Sending auth request to user-service on port 8001');
      return authApi.post(url, data, config).catch(handleApiError);
    } else {
      return taskApi.post(url, data, config).catch(handleApiError);
    }
  },
  
  // Task methods go to the task service
  get: (url, config) => taskApi.get(url, config).catch(handleApiError),
  patch: (url, data, config) => taskApi.patch(url, data, config).catch(handleApiError),
  delete: (url, config) => taskApi.delete(url, config).catch(handleApiError)
};

export default api;
