export const GoogleAuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadGoogleScript = () => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogleSignIn;
      document.body.appendChild(script);
    };

    const initializeGoogleSignIn = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
          callback: handleGoogleResponse
        });
      }
      setLoading(false);
    };

    const storedUser = sessionStorage.getItem('googleUser');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user:', e);
      }
    }

    loadGoogleScript();
  }, []);

  const handleGoogleResponse = async (response) => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: response.credential })
      });

      if (!res.ok) throw new Error('Google authentication failed');

      const userData = await res.json();
      setUser(userData);
      sessionStorage.setItem('googleUser', JSON.stringify(userData));
    } catch (err) {
      setError(err.message);
      console.error('Google sign-in error:', err);
    } finally {
      setLoading(false);
    }
  };

  const signInWithGoogle = () => {
    if (window.google) {
      window.google.accounts.id.prompt();
    } else {
      setError('Google Sign-In not loaded');
    }
  };

  const signOut = async () => {
    try {
      setLoading(true);
      
      if (window.google) {
        window.google.accounts.id.disableAutoSelect();
      }
      
      await fetch('/api/auth/logout', { method: 'POST' });
      
      setUser(null);
      sessionStorage.removeItem('googleUser');
      
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    loading,
    error,
    signInWithGoogle,
    signOut,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};