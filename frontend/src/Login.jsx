import { useState } from "react";
import { api } from "./api";

const rules = [
  { id: "len", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { id: "upper", label: "One uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { id: "lower", label: "One lowercase letter", test: (p) => /[a-z]/.test(p) },
  { id: "num", label: "One number", test: (p) => /\d/.test(p) },
  { id: "special", label: "One special character", test: (p) => /[^A-Za-z0-9]/.test(p) },
];

function PasswordStrength({ password }) {
  if (!password) return null;
  const passed = rules.filter((r) => r.test(password)).length;
  const pct = (passed / rules.length) * 100;
  const color = pct <= 40 ? "#e53e3e" : pct <= 70 ? "#dd6b20" : "#38a169";
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ height: 4, borderRadius: 4, background: "#e9e4f4", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, transition: "width .3s" }} />
      </div>
      <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
        {rules.map((r) => {
          const ok = r.test(password);
          return (
            <li key={r.id} style={{ fontSize: 11, color: ok ? "#38a169" : "#a0aec0", display: "flex", alignItems: "center", gap: 5 }}>
              <span>{ok ? "✓" : "○"}</span> {r.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function Login({ onLogin }) {
  const [tab, setTab] = useState("login");
  const [step, setStep] = useState("form"); // "form" | "otp"

  // login fields
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // signup fields
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // otp
  const [otp, setOtp] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");

  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const switchTab = (t) => { setTab(t); setError(""); setInfo(""); setStep("form"); };

  const allRulesPassed = rules.every((r) => r.test(password));
  const usernameValid = /^[a-zA-Z0-9_]{3,50}$/.test(username);
  const passwordsMatch = password === confirmPassword && confirmPassword !== "";

  const persist = (data) => {
    localStorage.setItem("td_token", data.access_token);
    localStorage.setItem("td_user", JSON.stringify({ username: data.username, role: data.role }));
    onLogin(data);
  };

  const submitLogin = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      persist(await api.login(loginUsername, loginPassword));
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  const submitSignup = async (e) => {
    e.preventDefault();
    setError("");
    if (!usernameValid) return setError("Username must be 3–50 characters, letters, numbers or underscores only.");
    if (!allRulesPassed) return setError("Password does not meet all requirements.");
    if (!passwordsMatch) return setError("Passwords do not match.");
    setLoading(true);
    try {
      const res = await api.signup(username, email, password);
      setPendingEmail(email);
      setStep("otp");
      setInfo(res.message || "Check your email for the verification code.");
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  const submitOtp = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      persist(await api.verifyOtp(pendingEmail, otp));
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  const resend = async () => {
    setError(""); setLoading(true);
    try {
      await api.resendOtp(pendingEmail);
      setInfo("A new code has been sent to your email.");
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  };

  // ── OTP screen ──────────────────────────────────────────────
  if (step === "otp") {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="eyebrow" style={{ color: "#9b7fe8", marginBottom: 6 }}>AI SUPPORT OPERATIONS</div>
          <h1 style={{ margin: "0 0 6px" }}>TrustDesk</h1>
          <p className="muted" style={{ marginBottom: 6 }}>Verify your email address</p>
          <p style={{ fontSize: 13, color: "#575267", marginBottom: 24 }}>
            We sent a 6-digit code to <b>{pendingEmail}</b>. Enter it below to activate your account.
          </p>
          {info && <div className="info-msg" style={{ marginBottom: 14 }}>{info}</div>}
          <form onSubmit={submitOtp}>
            <div className="field">
              <label>Verification code</label>
              <input
                type="text"
                inputMode="numeric"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                required
                autoFocus
                style={{ letterSpacing: "0.4em", fontSize: 24, textAlign: "center" }}
              />
              <span style={{ fontSize: 11, color: "#a0aec0", marginTop: 4 }}>Code expires in 10 minutes</span>
            </div>
            {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
            <button type="submit" disabled={loading || otp.length < 6} style={{ width: "100%", marginTop: 4 }}>
              {loading ? "Verifying…" : "Verify & activate account"}
            </button>
          </form>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
            <button type="button" className="link-btn" onClick={() => { setStep("form"); setOtp(""); setError(""); setInfo(""); }}>
              ← Back
            </button>
            <button type="button" className="link-btn" onClick={resend} disabled={loading}>
              Resend code
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Login / Signup form ──────────────────────────────────────
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="eyebrow" style={{ color: "#9b7fe8", marginBottom: 6 }}>AI SUPPORT OPERATIONS</div>
        <h1 style={{ margin: "0 0 18px" }}>TrustDesk</h1>

        <div className="auth-tabs">
          <button type="button" className={tab === "login" ? "auth-tab active" : "auth-tab"} onClick={() => switchTab("login")}>
            Sign in
          </button>
          <button type="button" className={tab === "signup" ? "auth-tab active" : "auth-tab"} onClick={() => switchTab("signup")}>
            Create account
          </button>
        </div>

        {/* ── LOGIN ── */}
        {tab === "login" && (
          <form onSubmit={submitLogin}>
            <div className="field">
              <label>Username</label>
              <input type="text" value={loginUsername} onChange={(e) => setLoginUsername(e.target.value)} placeholder="Enter username" required autoFocus />
            </div>
            <div className="field">
              <label>Password</label>
              <input type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
            <button type="submit" disabled={loading} style={{ width: "100%", marginTop: 4 }}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        )}

        {/* ── SIGNUP ── */}
        {tab === "signup" && (
          <form onSubmit={submitSignup}>
            <div className="field">
              <label>Username</label>
              <div style={{ position: "relative" }}>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="letters, numbers, underscores"
                  required
                  autoFocus
                  style={{ borderColor: username && !usernameValid ? "#e53e3e" : undefined }}
                />
                {username && (
                  <span style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", fontSize: 14 }}>
                    {usernameValid ? "✓" : "✗"}
                  </span>
                )}
              </div>
              {username && !usernameValid && (
                <span style={{ fontSize: 11, color: "#e53e3e" }}>3–50 chars, letters / numbers / underscores only</span>
              )}
            </div>

            <div className="field">
              <label>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
              <span style={{ fontSize: 11, color: "#a0aec0" }}>A verification code will be sent here</span>
            </div>

            <div className="field">
              <label>Password</label>
              <div style={{ position: "relative" }}>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  required
                  style={{ paddingRight: 44 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#9b7fe8", padding: 0, fontSize: 13, fontWeight: 700 }}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
              <PasswordStrength password={password} />
            </div>

            <div className="field">
              <label>Confirm password</label>
              <div style={{ position: "relative" }}>
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                  style={{ borderColor: confirmPassword && !passwordsMatch ? "#e53e3e" : confirmPassword && passwordsMatch ? "#38a169" : undefined, paddingRight: 44 }}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#9b7fe8", padding: 0, fontSize: 13, fontWeight: 700 }}
                >
                  {showConfirmPassword ? "Hide" : "Show"}
                </button>
                {confirmPassword && (
                  <span style={{ position: "absolute", right: 52, top: "50%", transform: "translateY(-50%)", fontSize: 14, color: passwordsMatch ? "#38a169" : "#e53e3e" }}>
                    {passwordsMatch ? "✓" : "✗"}
                  </span>
                )}
              </div>
              {confirmPassword && !passwordsMatch && (
                <span style={{ fontSize: 11, color: "#e53e3e" }}>Passwords do not match</span>
              )}
            </div>

            {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}

            <button
              type="submit"
              disabled={loading || !usernameValid || !allRulesPassed || !passwordsMatch}
              style={{ width: "100%", marginTop: 4 }}
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
