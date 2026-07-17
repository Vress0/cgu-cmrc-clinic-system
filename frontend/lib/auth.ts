"use client";

import type { TokenResponse, UserProfile } from "@/lib/api";

const ACCESS_TOKEN_KEY = "cgu_cmrc_access_token";
const REFRESH_TOKEN_KEY = "cgu_cmrc_refresh_token";
const USER_KEY = "cgu_cmrc_user";

export function saveSession(tokenResponse: TokenResponse): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokenResponse.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokenResponse.refresh_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(tokenResponse.user));
  window.dispatchEvent(new Event("auth:changed"));
}

export function clearSession(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event("auth:changed"));
}

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): UserProfile | null {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    clearSession();
    return null;
  }
}

export function dashboardPathForUser(user: UserProfile): string {
  if (user.roles.includes("registration")) {
    return "/registration";
  }
  if (user.roles.includes("clinic")) {
    return "/clinic";
  }
  if (user.roles.includes("pharmacy")) {
    return "/pharmacy";
  }
  return "/dashboard";
}
