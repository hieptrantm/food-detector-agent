"use client";

import { useAuthGoogleLoginService } from "./useAuthService";
import { useAuthActions } from "./useAuth";
import { useAuthTokens } from "./useAuth";
import { GoogleLogin } from "@react-oauth/google";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function GoogleAuth() {
  const { setUser, refreshUser } = useAuthActions();
  const { setTokensInfo } = useAuthTokens();
  const authGoogleLoginService = useAuthGoogleLoginService();
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const onSuccess = async (tokenResponse) => {
    console.log(tokenResponse);
    if (!tokenResponse.credential) return;
    setIsLoading(true);

    const result = await authGoogleLoginService({
      id_token: tokenResponse.credential,
    });

    setTokensInfo({
      token: result.access_token,
      refreshToken: result.refresh_token,
      tokenExpires: result.expires_at,
    });
    setUser(result.user);
    await refreshUser();
    setIsLoading(false);
    navigate("/");
  };

  return (
    <GoogleLogin
      onSuccess={onSuccess}
      locale="vi"
      size="large"
      width="350"
      logo_alignment="left"
      theme="outline"
    />
  );
}
