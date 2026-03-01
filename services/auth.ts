/**
 * Authentication Service
 * Handle user login, registration, and token management
 */

import { authAPI } from "./api";

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
  ): Promise<User> {
    const response = await authAPI.register(name, email, password);
    return response;
  }

  async login(email: string, password: string): Promise<AuthToken> {
    const response = await authAPI.login(email, password);
    this.setToken(response.access_token);
    if (response.user) {
      this.setUser(response.user);
    }
    return response;
  }

  async getProfile(): Promise<User> {
    if (!this.token) throw new Error("No token available");
    const user = await authAPI.getProfile();
    this.setUser(user);
    return user;
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("access_token", token);
  }

  setUser(user: User) {
    this.user = user;
    localStorage.setItem("user", JSON.stringify(user));
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
  }
}

export default new AuthService();
