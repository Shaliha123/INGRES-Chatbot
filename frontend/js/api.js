// INGRES Live Backend API Client Module
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function formatErrorMessage(data, status) {
  if (!data) return `HTTP ${status} Error`;
  
  let msg = data.detail || data.message || data.error;
  if (Array.isArray(msg)) {
    return msg.map(item => item.msg || item.message || (typeof item === 'object' ? JSON.stringify(item) : String(item))).join("; ");
  } else if (typeof msg === 'object' && msg !== null) {
    return msg.message || msg.msg || JSON.stringify(msg);
  } else if (typeof msg === 'string' && msg.trim().length > 0) {
    return msg;
  }
  
  return `HTTP ${status} Error`;
}

export class APIClient {
  static getAuthToken() {
    return localStorage.getItem("ingres_access_token") || "";
  }

  static setAuthToken(token) {
    localStorage.setItem("ingres_access_token", token);
  }

  static removeAuthToken() {
    localStorage.removeItem("ingres_access_token");
    localStorage.removeItem("ingres_user");
  }

  static getHeaders(isMultipart = false) {
    const headers = {};
    if (!isMultipart) {
      headers["Content-Type"] = "application/json";
    }
    const token = this.getAuthToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  static async request(endpoint, method = "GET", body = null, isMultipart = false) {
    const url = `${API_BASE_URL}${endpoint}`;
    const options = {
      method,
      headers: this.getHeaders(isMultipart)
    };

    if (body) {
      options.body = isMultipart ? body : JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      let data = null;
      try {
        data = await response.json();
      } catch (e) {
        // Response was not JSON
      }

      if (!response.ok) {
        const errorMsg = formatErrorMessage(data, response.status);
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Request Error [${method} ${endpoint}]:`, err);
      throw err;
    }
  }

  // --- Auth APIs ---
  static async register(name, email, password, role = "User") {
    const res = await this.request("/register", "POST", { name, email, password, role });
    if (res.success && res.data && res.data.access_token) {
      this.setAuthToken(res.data.access_token);
      localStorage.setItem("ingres_user", JSON.stringify(res.data.user));
    }
    return res;
  }

  static async login(email, password) {
    const res = await this.request("/login", "POST", { email, password });
    if (res.success && res.data && res.data.access_token) {
      this.setAuthToken(res.data.access_token);
      localStorage.setItem("ingres_user", JSON.stringify(res.data.user));
    }
    return res;
  }

  static async getProfile() {
    return await this.request("/profile", "GET");
  }

  static async logout() {
    try {
      await this.request("/logout", "POST");
    } finally {
      this.removeAuthToken();
    }
  }

  // --- Chat & RAG APIs ---
  static async sendChatMessage(question, conversationId = null) {
    return await this.request("/chat", "POST", { question, conversation_id: conversationId });
  }

  static async getChatHistory(conversationId = null) {
    const query = conversationId ? `?conversation_id=${conversationId}` : "";
    return await this.request(`/chat/history${query}`, "GET");
  }

  // --- Knowledge Base APIs ---
  static async listKnowledge(query = "", category = "") {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (category) params.append("category", category);
    const queryString = params.toString() ? `?${params.toString()}` : "";
    return await this.request(`/knowledge${queryString}`, "GET");
  }

  static async createKnowledge(title, category, content, keywords = [], source = "INGRES Portal") {
    return await this.request("/knowledge", "POST", { title, category, content, keywords, source });
  }

  // --- Documents APIs ---
  static async uploadDocument(formData) {
    return await this.request("/documents", "POST", formData, true);
  }

  static async listDocuments() {
    return await this.request("/documents", "GET");
  }

  static async deleteDocument(docId) {
    return await this.request(`/documents/${docId}`, "DELETE");
  }

  // --- Dashboard & Analytics APIs ---
  static async getDashboard() {
    return await this.request("/dashboard", "GET");
  }

  static async getAnalytics() {
    return await this.request("/analytics", "GET");
  }

  // --- Settings APIs ---
  static async getSettings() {
    return await this.request("/settings", "GET");
  }

  static async updateSettings(settingsData) {
    return await this.request("/settings", "PUT", settingsData);
  }

  // --- Admin APIs ---
  static async listUsers() {
    return await this.request("/users", "GET");
  }

  static async getAdminLogs() {
    return await this.request("/admin/logs", "GET");
  }
}

export default APIClient;
