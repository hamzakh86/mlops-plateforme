css = """
/* ─── LOGIN PAGE ──────────────────────────────────────────────────────────── */
.login-shell {
  display: grid;
  place-items: center;
  min-height: 100vh;
  width: 100%;
  position: fixed;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 45%, #0f4c75 100%);
}
.login-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(15,118,110,0.35) 0%, transparent 55%),
    radial-gradient(ellipse at 80% 80%, rgba(37,99,235,0.3) 0%, transparent 55%),
    radial-gradient(ellipse at 60% 10%, rgba(99,102,241,0.2) 0%, transparent 45%);
  animation: lgBg 8s ease-in-out infinite alternate;
}
@keyframes lgBg {
  0%   { opacity: 0.7; transform: scale(1); }
  100% { opacity: 1;   transform: scale(1.06); }
}
.login-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 44px 40px;
  background: rgba(255,255,255,0.07);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px;
  box-shadow: 0 32px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05) inset, 0 2px 0 rgba(255,255,255,0.12) inset;
  animation: lgCardIn 0.5s cubic-bezier(0.34,1.56,0.64,1) both;
}
@keyframes lgCardIn {
  from { opacity: 0; transform: translateY(30px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.login-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  margin-bottom: 32px;
  text-align: center;
}
.login-logo img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  filter: drop-shadow(0 4px 16px rgba(15,118,110,0.5));
  animation: lgFloat 3s ease-in-out infinite;
}
@keyframes lgFloat {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-5px); }
}
.login-logo span {
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #5eead4;
  margin-bottom: 4px;
}
.login-logo strong {
  display: block;
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
}
.login-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  margin-bottom: 28px;
}
.login-form {
  display: grid;
  gap: 18px;
}
.login-field {
  display: grid;
  gap: 8px;
}
.login-field-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: rgba(255,255,255,0.65);
  letter-spacing: 0.8px;
  text-transform: uppercase;
}
.login-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  color: #ffffff;
  font-size: 0.95rem;
  transition: all 0.25s ease;
}
.login-input::placeholder { color: rgba(255,255,255,0.3); }
.login-input:focus {
  outline: none;
  background: rgba(255,255,255,0.13);
  border-color: rgba(94,234,212,0.5);
  box-shadow: 0 0 0 3px rgba(94,234,212,0.12);
}
.login-btn {
  margin-top: 8px;
  height: 50px;
  width: 100%;
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%);
  border: none;
  border-radius: 10px;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(15,118,110,0.5);
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(15,118,110,0.65);
}
.login-error {
  padding: 12px 14px;
  background: rgba(180,35,24,0.2);
  border: 1px solid rgba(180,35,24,0.4);
  border-radius: 8px;
  color: #fca5a5;
  font-size: 0.84rem;
  font-weight: 600;
  text-align: center;
}
.login-hint {
  margin-top: 20px;
  text-align: center;
  font-size: 0.78rem;
  color: rgba(255,255,255,0.35);
}
.login-hint kbd {
  display: inline-block;
  padding: 2px 7px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 4px;
  font-family: inherit;
  color: rgba(255,255,255,0.6);
}
"""

with open("frontend/src/styles.css", "a", encoding="utf-8") as f:
    f.write(css)

print("Login CSS appended successfully!")
