"use client";

import { useCallback } from "react";
import { getTokensInfo, setTokensInfo } from "./token";

async function fetchWithAuth(url, options = {}) {
  let tokens = getTokensInfo();

  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  if (tokens?.tokenExpires && tokens.tokenExpires - 60000 <= Date.now()) {
    const res = await fetch(`/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refreshToken }),
    });

    if (res.ok) {
      const newTokens = await res.json();
      tokens = {
        token: newTokens.access_token,
        refreshToken: newTokens.refresh_token,
        tokenExpires: newTokens.expires_at,
      };
      setTokensInfo(tokens);
    } else {
      setTokensInfo(null);
      throw new Error("Session expired");
    }
  }

  if (tokens?.token) {
    headers.set("Authorization", `Bearer ${tokens.token}`);
  }

  const response = await fetch(url, { ...options, headers });
  return response;
}

export function useAuthLoginService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error("Login failed");
    const result = await res.json();

    setTokensInfo({
      token: result.access_token,
      refreshToken: result.refresh_token,
      tokenExpires: result.expires_at,
    });

    return result;
  }, []);
}

export function useAuthSignUpService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error("Register failed");
    return res.json();
  }, []);
}

export function useAuthGetMeService() {
  return useCallback(async () => {
    const res = await fetchWithAuth(`/auth/me`);
    if (!res.ok) throw new Error("Failed to fetch user");
    return res.json();
  }, []);
}

export function useAuthPatchMeService() {
  return useCallback(async (data) => {
    const res = await fetchWithAuth(`/auth/me`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Update failed");
    return res.json();
  }, []);
}

export function useAuthLogoutService() {
  return useCallback(async () => {
    await fetchWithAuth(`/auth/logout`, { method: "POST" });
    setTokensInfo(null);
  }, []);
}

export function useAuthConfirmEmailService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/email/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Email confirmation failed");
    return res.json();
  }, []);
}

export function useAuthConfirmNewEmailService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/email/confirm/new`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("New email confirmation failed");
    return res.json();
  }, []);
}

export function useAuthGoogleLoginService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/google/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error("Google login failed");
    const result = await res.json();

    setTokensInfo({
      token: result.access_token,
      refreshToken: result.refresh_token,
      tokenExpires: result.expires_at,
    });

    return result;
  }, []);
}

export function useAuthResetPasswordService() {
  return useCallback(async (data) => {
    const res = await fetch(`/auth/reset/password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Password reset failed");
    return res.json();
  }, []);
}
