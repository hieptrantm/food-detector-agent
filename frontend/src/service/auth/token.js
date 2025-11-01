import Cookies from "js-cookie";

export function getTokensInfo() {
  try {
    return JSON.parse(Cookies.get('auth-token-data') ?? "null");
  } catch {
    return null;
  }
}

export function setTokensInfo(tokens) {
  if (tokens) {
    Cookies.set('auth-token-data', JSON.stringify(tokens), { sameSite: "strict" });
  } else {
    Cookies.remove('auth-token-data');
  }
}