import { useContext } from "react";
import { AuthContext, AuthActionsContext, AuthTokensContext } from "./authContext.js";

export function useAuth() {
  return useContext(AuthContext);
}

export function useAuthActions() {
  return useContext(AuthActionsContext);
}

export function useAuthTokens() {
  return useContext(AuthTokensContext);
}
