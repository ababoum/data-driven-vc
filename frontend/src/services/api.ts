import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkApiStatus = async () => {
  try {
    const response = await api.get('/');
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const analyzeDomain = async (domain: string) => {
  try {
    const response = await api.post('/analyze-domain', { domain });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getJobStatus = async (jobId: string) => {
  try {
    const response = await api.get(`/job/${jobId}`);
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const summarizeStep = async (stepData: any) => {
  try {
    const response = await api.post('/summarize-step', { step_data: stepData });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export default api; 