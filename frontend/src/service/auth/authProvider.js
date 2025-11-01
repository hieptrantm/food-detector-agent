"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AuthActionsContext,
  AuthContext,
  AuthTokensContext,
} from "./authContext";
import useFetch from "./useFetch.js";
import { getTokensInfo, setTokensInfo as setTokensInfoToStorage } from "./token.js";

// enum HTTP_CODES_ENUM {
//   OK = 200,
//   CREATED = 201,
//   ACCEPTED = 202,
//   NO_CONTENT = 204,
//   BAD_REQUEST = 400,
//   UNAUTHORIZED = 401,
//   FORBIDDEN = 403,
//   NOT_FOUND = 404,
//   UNPROCESSABLE_ENTITY = 422,
//   INTERNAL_SERVER_ERROR = 500,
//   SERVICE_UNAVAILABLE = 503,
//   GATEWAY_TIMEOUT = 504,
// }

function AuthProvider(props) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [user, setUser] = useState(null);
  const fetchBase = useFetch();

  const setTokensInfo = useCallback((tokensInfo) => {
    setTokensInfoToStorage(tokensInfo);

    if (!tokensInfo) {
      setUser(null);
    }
  }, []);

  const logOut = useCallback(async () => {
    const tokens = getTokensInfo();

    if (tokens?.token) {
      await fetchBase('/auth/logout', {
        method: "POST",
      });
    }
    setTokensInfo(null);
  }, [setTokensInfo, fetchBase]);

  const loadData = useCallback(async () => {
    const tokens = getTokensInfo();

    try {
      if (tokens?.token) {
        const response = await fetchBase('/auth/me', {
          method: "GET",
        });

        if (response.status === 401) {
          logOut();
          return;
        }

        const data = await response.json();
        console.log("User data loaded:", data);
        setUser(data);
      }
    } finally {
      setIsLoaded(true);
    }
  }, [fetchBase, logOut]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const contextValue = useMemo(
    () => ({
      isLoaded,
      user,
    }),
    [isLoaded, user]
  );

  const contextActionsValue = useMemo(
    () => ({
      setUser,
      logOut,
    }),
    [logOut]
  );

  const contextTokensValue = useMemo(
    () => ({
      setTokensInfo,
    }),
    [setTokensInfo]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      <AuthActionsContext.Provider value={contextActionsValue}>
        <AuthTokensContext.Provider value={contextTokensValue}>
          {props.children}
        </AuthTokensContext.Provider>
      </AuthActionsContext.Provider>
    </AuthContext.Provider>
  );
}

export default AuthProvider;
