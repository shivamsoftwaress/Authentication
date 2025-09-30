import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const authAPI = {
  signup: (data) => axios.post(`${API}/auth/signup`, data),
  verifySignup: (data) => axios.post(`${API}/auth/verify-signup`, data),
  loginPassword: (data) => axios.post(`${API}/auth/login/password`, data),
  verifyLoginOTP: (data) => axios.post(`${API}/auth/login/verify-otp`, data),
  logout: (data, token) => axios.post(`${API}/auth/logout`, data, {
    headers: { Authorization: `Bearer ${token}` }
  }),
};

export const userAPI = {
  getMe: (token) => axios.get(`${API}/users/me`, {
    headers: { Authorization: `Bearer ${token}` }
  }),
};

export const adminAPI = {
  getAllUsers: (token) => axios.get(`${API}/admin/users`, {
    headers: { Authorization: `Bearer ${token}` }
  }),
  getStats: (token) => axios.get(`${API}/admin/stats`, {
    headers: { Authorization: `Bearer ${token}` }
  }),
};

export const customerAPI = {
  getProfile: (token) => axios.get(`${API}/customer/profile`, {
    headers: { Authorization: `Bearer ${token}` }
  }),
};