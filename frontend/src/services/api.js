import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.patch('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  deleteAccount: (data) => api.delete('/auth/me', { data }),
};

// Wikis API
export const wikisAPI = {
  list: () => api.get('/wikis'),
  listPublic: (params = {}) => axios.get(`${API_BASE}/wikis/public`, { params }), // No auth required
  create: (data) => api.post('/wikis', data),
  get: (id, includePages = false) => api.get(`/wikis/${id}`, { params: { include_pages: includePages } }),
  update: (id, data) => api.patch(`/wikis/${id}`, data),
  delete: (id) => api.delete(`/wikis/${id}`),
  
  // Members
  listMembers: (wikiId) => api.get(`/wikis/${wikiId}/members`),
  addMember: (wikiId, data) => api.post(`/wikis/${wikiId}/members`, data),
  updateMember: (wikiId, userId, data) => api.patch(`/wikis/${wikiId}/members/${userId}`, data),
  removeMember: (wikiId, userId) => api.delete(`/wikis/${wikiId}/members/${userId}`),
  
  // Bulk import
  importArchive: (formData, onProgress) => {
    return api.post('/wikis/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    });
  },
  importToExisting: (wikiId, formData, onProgress) => {
    return api.post(`/wikis/${wikiId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    });
  },
  getPageTree: (wikiId) => api.get(`/wikis/${wikiId}/pages/tree`),
};

// Pages API
export const pagesAPI = {
  list: (wikiId, structure = 'flat') => api.get(`/wikis/${wikiId}/pages`, { params: { structure } }),
  create: (wikiId, data) => api.post(`/wikis/${wikiId}/pages`, data),
  get: (wikiId, pageId, includeChildren = false) => 
    api.get(`/wikis/${wikiId}/pages/${pageId}`, { params: { include_children: includeChildren } }),
  getByPath: (wikiId, path) => api.get(`/wikis/${wikiId}/pages/by-path/${path}`),
  update: (wikiId, pageId, data) => api.patch(`/wikis/${wikiId}/pages/${pageId}`, data),
  delete: (wikiId, pageId) => api.delete(`/wikis/${wikiId}/pages/${pageId}`),
  move: (wikiId, pageId, data) => api.post(`/wikis/${wikiId}/pages/${pageId}/move`, data),
  getChildren: (wikiId, pageId) => api.get(`/wikis/${wikiId}/pages/${pageId}/children`),
  
  // Revisions
  getRevisions: (wikiId, pageId) => api.get(`/wikis/${wikiId}/pages/${pageId}/revisions`),
  getRevision: (wikiId, pageId, revisionId) => 
    api.get(`/wikis/${wikiId}/pages/${pageId}/revisions/${revisionId}`),
  restoreRevision: (wikiId, pageId, revisionId) => 
    api.post(`/wikis/${wikiId}/pages/${pageId}/restore/${revisionId}`),
};

// Attachments API
export const attachmentsAPI = {
  list: (wikiId, pageId) => api.get(`/wikis/${wikiId}/pages/${pageId}/attachments`),
  listAll: (wikiId) => api.get(`/wikis/${wikiId}/attachments`),
  upload: (wikiId, pageId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/wikis/${wikiId}/pages/${pageId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadImage: (wikiId, pageId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/wikis/${wikiId}/pages/${pageId}/upload-image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  get: (attachmentId) => api.get(`/attachments/${attachmentId}`),
  delete: (attachmentId) => api.delete(`/attachments/${attachmentId}`),
  getDownloadUrl: (attachmentId) => {
    const token = localStorage.getItem('access_token');
    return `/api/attachments/${attachmentId}/download${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
  getViewUrl: (attachmentId) => {
    const token = localStorage.getItem('access_token');
    return `/api/attachments/${attachmentId}/view${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
};

// Search API
export const searchAPI = {
  searchPages: (query, wikiId = null, limit = 20, offset = 0) => 
    api.get('/search/pages', { params: { q: query, wiki_id: wikiId, limit, offset } }),
  searchWikiPages: (wikiId, query, limit = 20, offset = 0) => 
    api.get(`/search/wikis/${wikiId}/pages`, { params: { q: query, limit, offset } }),
  searchUsers: (query, limit = 10) => 
    api.get('/search/users', { params: { q: query, limit } }),
  
  // Semantic search
  semanticSearch: (query, wikiId = null, limit = 20, offset = 0, threshold = 0.5) =>
    api.get('/search/semantic', { params: { q: query, wiki_id: wikiId, limit, offset, threshold } }),
  hybridSearch: (query, wikiId = null, limit = 20, semanticWeight = 0.7) =>
    api.get('/search/hybrid', { params: { q: query, wiki_id: wikiId, limit, semantic_weight: semanticWeight } }),
};

// Tags API
export const tagsAPI = {
  list: (wikiId) => api.get(`/wikis/${wikiId}/tags`),
  create: (wikiId, data) => api.post(`/wikis/${wikiId}/tags`, data),
  update: (wikiId, tagId, data) => api.patch(`/wikis/${wikiId}/tags/${tagId}`, data),
  delete: (wikiId, tagId) => api.delete(`/wikis/${wikiId}/tags/${tagId}`),
  verify: (wikiId, tagId) => api.post(`/wikis/${wikiId}/tags/${tagId}/verify`),
  
  // Page tags
  getPageTags: (wikiId, pageId) => api.get(`/wikis/${wikiId}/pages/${pageId}/tags`),
  addTagToPage: (wikiId, pageId, tagId) => api.post(`/wikis/${wikiId}/pages/${pageId}/tags/${tagId}`),
  removeTagFromPage: (wikiId, pageId, tagId) => api.delete(`/wikis/${wikiId}/pages/${pageId}/tags/${tagId}`),
};

// Admin API
export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  listUsers: (params = {}) => api.get('/admin/users', { params }),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  updateUser: (userId, data) => api.patch(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  
  // Pending user approvals
  listPendingUsers: (params = {}) => api.get('/admin/pending-users', { params }),
  approveUser: (userId) => api.post(`/admin/users/${userId}/approve`),
  rejectUser: (userId) => api.post(`/admin/users/${userId}/reject`),
  
  // Embeddings management
  listPendingEmbeddings: (params = {}) => api.get('/admin/embeddings/pending', { params }),
  generatePageEmbedding: (pageId) => api.post(`/admin/embeddings/generate/${pageId}`),
  generateAllEmbeddings: (data = {}) => api.post('/admin/embeddings/generate-all', data),
  
  // Wiki management
  listWikis: (params = {}) => api.get('/admin/wikis', { params }),
  deleteWiki: (wikiId) => api.delete(`/admin/wikis/${wikiId}`),
  transferWikiOwnership: (wikiId, data) => api.post(`/admin/wikis/${wikiId}/transfer`, data),
};

export default api;
