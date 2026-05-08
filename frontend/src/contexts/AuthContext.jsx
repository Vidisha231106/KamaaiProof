import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { supabase } from "../services/supabaseClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!mounted) return;
        setSession(data?.session ?? null);
        setUser(data?.session?.user ?? null);
        setAuthReady(true);
      })
      .catch(() => {
        if (!mounted) return;
        setAuthReady(true);
      });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      if (!mounted) return;
      setSession(newSession);
      setUser(newSession?.user ?? null);
    });

    return () => {
      mounted = false;
      listener?.subscription?.unsubscribe();
    };
  }, []);

  const signInWithGoogle = async () => {
    const origin = window.location.origin;
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${origin}/upload`,
      },
    });
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const value = useMemo(
    () => ({
      session,
      user,
      authReady,
      signInWithGoogle,
      signOut,
    }),
    [session, user, authReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
