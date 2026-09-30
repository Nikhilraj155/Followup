import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for JWT auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const authService = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  register: async (name, email, password) => {
    const response = await api.post('/auth/register', { name, email, password });
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  getGoogleAuthUrl: async () => {
    const response = await api.get('/auth/google');
    return response.data;
  },
  googleCallback: async (code) => {
    const response = await api.get(`/auth/google/callback?code=${code}`);
    return response.data;
  },
  connectGmailDirect: async (email = null) => {
    const response = await api.post('/auth/google/connect', { email });
    return response.data;
  },
  logout: async () => {
    await api.post('/auth/logout');
  }
};

export const applicationService = {
  getApplications: async (statusFilter = '') => {
    const url = statusFilter ? `/applications?status_filter=${statusFilter}` : '/applications';
    const response = await api.get(url);
    return response.data;
  },
  getApplication: async (id) => {
    const response = await api.get(`/applications/${id}`);
    return response.data;
  },
  createApplication: async (data) => {
    const response = await api.post('/applications', data);
    return response.data;
  },
  updateApplication: async (id, data) => {
    const response = await api.put(`/applications/${id}`, data);
    return response.data;
  },
  deleteApplication: async (id) => {
    const response = await api.delete(`/applications/${id}`);
    return response.data;
  }
};

export const emailService = {
  sendApplicationEmail: async (formData) => {
    const response = await api.post('/emails/send', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  getThread: async (threadId) => {
    const response = await api.get(`/emails/threads/${threadId}`);
    return response.data;
  },
  syncInbox: async () => {
    const response = await api.post('/emails/sync-inbox');
    return response.data;
  },
  getAllEmails: async (typeFilter = '') => {
    const url = typeFilter ? `/emails/all?type_filter=${typeFilter}` : '/emails/all';
    const response = await api.get(url);
    return response.data;
  }
};

export const followupService = {
  getFollowups: async (statusFilter = '') => {
    const url = statusFilter ? `/followups?status_filter=${statusFilter}` : '/followups';
    const response = await api.get(url);
    return response.data;
  },
  getFollowup: async (id) => {
    const response = await api.get(`/followups/${id}`);
    return response.data;
  },
  generateFollowup: async (id) => {
    const response = await api.post(`/followups/${id}/generate`);
    return response.data;
  },
  updateFollowup: async (id, data) => {
    const response = await api.put(`/followups/${id}`, data);
    return response.data;
  },
  approveFollowup: async (id) => {
    const response = await api.post(`/followups/${id}/approve`);
    return response.data;
  },
  sendFollowupNow: async (id) => {
    const response = await api.post(`/followups/${id}/send`);
    return response.data;
  },
  cancelFollowup: async (id) => {
    const response = await api.post(`/followups/${id}/cancel`);
    return response.data;
  }
};

export const settingsService = {
  getSettings: async () => {
    const response = await api.get('/settings');
    return response.data;
  },
  updateSettings: async (data) => {
    const response = await api.put('/settings', data);
    return response.data;
  }
};

export const dashboardService = {
  getStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  }
};

export default api;
