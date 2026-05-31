/**
 * Authentication Service
 * Handle user login, registration, and token management
 */

import { authAPI } from "./api";
import { DEMO_LOGIN } from "../demoConfig";

export interface User {
  id: string;
  name: string;
  email: string;
  role: "user" | "admin";
  energy_limit: number;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user?: User;
}

class AuthService {
  private token: string | null = null;
  private user: User | null = null;
  private listeners: Set<() => void> = new Set();

  constructor() {
    this.token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    if (userStr) {
      this.user = JSON.parse(userStr);
    }
  }

  async register(
    name: string,
    email: string,
    password: string
  ): Promise<AuthToken> {
    const response = await authAPI.register(name, email, password);

    if (response.access_token) {
      this.setToken(response.access_token);
    }
    if (response.user) {
      this.setUser(response.user);
    }

    return response as AuthToken;
  }

  async login(email: string, password: string): Promise<AuthToken> {
    if (DEMO_LOGIN) {
      try {
        // Try real login with admin credentials
        const response = await authAPI.login("admin@aipeco.com", "admin123");
        this.setToken(response.access_token);
        if (response.user) {
          this.setUser(response.user);
        }
        return response;
      } catch (err) {
        // If it fails, fallback to trying the user provided or creating an error
        console.warn("Demo login with admin credentials failed. Ensure db is seeded.");
      }
    }

    const response = await authAPI.login(email, password);
    this.setToken(response.access_token);
    if (response.user) {
      this.setUser(response.user);
    } else {
      const profile = await this.getProfile();
      this.setUser(profile);
    }
    return response;
  }

  async getProfile(): Promise<User> {
    if (!this.token) throw new Error("No token available");
    const user = await authAPI.getProfile();
    this.setUser(user);
    return user;
  }

  async forgotPassword(email: string): Promise<any> {
    try {
      const res = await authAPI.forgotPassword(email);
      return res;
    } catch (err) {
      throw err;
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<any> {
    try {
      const res = await authAPI.resetPassword(token, newPassword);
      return res;
    } catch (err) {
      throw err;
    }
  }

  subscribe(listener: () => void) {
    this.listeners.add(listener);
  }

  unsubscribe(listener: () => void) {
    this.listeners.delete(listener);
  }

  private emitAuthChange() {
    this.listeners.forEach((listener) => listener());
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("access_token", token);
    this.emitAuthChange();
  }

  setUser(user: User) {
    this.user = user;
    localStorage.setItem("user", JSON.stringify(user));
    this.emitAuthChange();
  }

  getToken(): string | null {
    return this.token;
  }

  getUser(): User | null {
    return this.user;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    this.emitAuthChange();
  }
}

export default new AuthService();
