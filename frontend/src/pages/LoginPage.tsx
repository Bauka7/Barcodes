import { Barcode } from "lucide-react";
import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { getErrorMessage } from "../api/http";
import { useAuth } from "../auth/AuthProvider";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { useI18n } from "../i18n";

interface LocationState {
  from?: {
    pathname: string;
  };
}

export function LoginPage() {
  const { login, user } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/app/departments" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(username.trim(), password);
      const state = location.state as LocationState | null;
      navigate(state?.from?.pathname ?? "/app/departments", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <div className="login-mark">
            <Barcode size={28} />
          </div>
          <div>
            <h1>{t("appName")}</h1>
            <p>Генерация и печать штрихкодов</p>
          </div>
        </div>

        <Input
          autoComplete="username"
          label={t("username")}
          name="username"
          placeholder="admin"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
        <Input
          autoComplete="current-password"
          label={t("password")}
          name="password"
          placeholder="••••••••"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {error ? <div className="alert alert-danger">{error}</div> : null}

        <Button className="full-width" loading={loading} type="submit" variant="primary">
          {t("login")}
        </Button>
      </form>
    </main>
  );
}
