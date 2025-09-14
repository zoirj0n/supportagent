import { useEffect, useMemo, useState } from "react";

const API = "http://localhost:8000";

type Account = {
  id: string;
  gmail_address: string;
  is_active: boolean;
  is_primary?: boolean;
  connected_at?: string | null;
  disconnected_at?: string | null; // NEW
};

type AccountDetails = {
  id: string;
  gmail_address: string;
  is_active: boolean;
  is_primary?: boolean;
  connected_at?: string | null;
  disconnected_at?: string | null;   // NEW
  google_user_id?: string | null;
  scopes?: string[];
};

export default function App() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [details, setDetails] = useState<AccountDetails | null>(null);

  async function load() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/accounts/`);
      const j = (await r.json()) as Account[];
      setAccounts(j ?? []);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  const primaryId = useMemo(
    () => accounts.find(a => a.is_primary)?.id ?? accounts[0]?.id ?? null,
    [accounts]
  );

  async function disconnect(id: string) {
    if (!confirm("Disconnect this Gmail account?")) return;
    setBusy(id);
    try {
      await fetch(`${API}/accounts/${id}`, { method: "DELETE" });
      await load();
    } finally {
      setBusy(null);
    }
  }

  async function openDetails(id: string) {
    try {
      const r = await fetch(`${API}/accounts/${encodeURIComponent(id)}`);
      if (r.ok) {
        const j = (await r.json()) as AccountDetails;
        setDetails({
          id: j.id,
          gmail_address: j.gmail_address,
          is_active: j.is_active,
          connected_at: j.connected_at ?? null,
          disconnected_at: j.disconnected_at ?? null, // NEW
          google_user_id: j.google_user_id ?? null,
          scopes: j.scopes && j.scopes.length ? j.scopes : [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
          ],
        });
        return;
      }
    } catch { /* ignore */ }

    // fallback to list data
    const a = accounts.find(x => x.id === id);
    if (a) {
      setDetails({
        id: a.id,
        gmail_address: a.gmail_address,
        is_active: a.is_active,
        connected_at: a.connected_at ?? null,
        disconnected_at: a.disconnected_at ?? null, // NEW
        scopes: [
          "https://www.googleapis.com/auth/gmail.modify",
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/userinfo.profile",
          "openid",
        ],
      });
    }
  }

  return (
    <div className="ga-wrap">
      <Style />

      <header className="ga-top">
        <div>
          <h1>Gmail Accounts</h1>
        <p className="ga-muted">Manage your connected Gmail accounts</p>
        </div>
        <a className="ga-add" href={`${API}/auth/google/start`}>+ Add Gmail</a>
      </header>

      {loading ? (
        <div className="ga-card ga-skeleton" />
      ) : (
        <div className="ga-list">
          {accounts.map(a => (
            <div className="ga-card" key={a.id}>
              <div className="ga-left">
                <div className="ga-gmail">
                  <GmailIcon/>
                </div>
                <div>
                  <div className="ga-row">
                    <span className="ga-email">{a.gmail_address}</span>
                    {(a.is_primary || a.id === primaryId) && (
                      <span className="ga-badge">Primary</span>
                    )}
                  </div>

                  <div className="ga-muted">
                    {a.is_active
                      ? (a.connected_at ? `Connected ${formatCardDate(a.connected_at)}` : "Connected")
                      : (a.disconnected_at ? `Disconnected ${formatCardDate(a.disconnected_at)}` : "Disconnected")}
                  </div>
                </div>
              </div>

              <div className="ga-actions">
                <button className="ga-btn" onClick={() => openDetails(a.id)}>
                  <span>Details</span>
                </button>
                <button
                  className="ga-danger"
                  disabled={!a.is_active || busy === a.id}
                  onClick={() => disconnect(a.id)}
                >
                  <span>{busy === a.id ? "Disconnecting…" : "Disconnect"}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ===== Details Modal ===== */}
      {details && (
        <div className="ga-backdrop" onClick={() => setDetails(null)}>
          <div className="ga-modal" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true">
            <div className="ga-modal-head">
              <div className="ga-left">
                <div className="ga-gmail sm"><GmailIcon/></div>
                <div>
                  <div className="ga-row">
                    <span className="ga-email">{details.gmail_address}</span>
                    {(details.is_primary || details.id === primaryId) && (
                      <span className="ga-badge">Primary</span>
                    )}
                  </div>
                  <div className="ga-muted">Account Details</div>
                </div>
              </div>
              <button className="ga-x" onClick={() => setDetails(null)} aria-label="Close">×</button>
            </div>

            <div className="ga-modal-body">
              <div className="ga-field">
                <div className="ga-label">Status</div>
                <div className="ga-value">
                  {details.is_active
                    ? "Active"
                    : (details.disconnected_at ? `Disconnected ${formatModalDate(details.disconnected_at)}` : "Disconnected")}
                </div>
              </div>
              <br />
              <div className="ga-field">
                <div className="ga-label">Connected since</div>
                <div className="ga-value">
                  {details.connected_at ? formatModalDate(details.connected_at) : "Unknown"}
                </div>
              </div>
              {!details.is_active && (
                <>
                  <br />
                  <div className="ga-field">
                    <div className="ga-label">Disconnected at</div>
                    <div className="ga-value">
                      {details.disconnected_at ? formatModalDate(details.disconnected_at) : "Unknown"}
                    </div>
                  </div>
                </>
              )}
              <br />
              <div className="ga-field">
                <div className="ga-label">Granted Permissions</div>
                <ul className="ga-perms">
                  {(details.scopes ?? [
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "openid",
                  ]).map(s => (
                    <li key={s}><span className="ga-dot" /> {humanizeScope(s)}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="ga-modal-foot">
              <button className="ga-danger wide" disabled={!details.is_active} onClick={() => disconnect(details.id)}>
                Disconnect Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ===== Helpers & Icons ===== */
function formatCardDate(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}
function formatModalDate(iso?: string | null) {
  if (!iso) return "Unknown";
  const d = new Date(iso);
  const date = d.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  return `${date} at ${time}`;
}
function humanizeScope(scope: string) {
  if (scope.includes("gmail.readonly")) return "Gmail Read-only";
  if (scope.includes("gmail.modify")) return "Gmail Modify";
  if (scope.includes("/userinfo.email") || scope === "email") return "Email Address";
  if (scope.includes("/userinfo.profile") || scope === "profile") return "Basic Profile";
  if (scope === "openid") return "OpenID";
  return scope;
}

const GmailIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden>
    <path fill="#EA4335" d="M12 13.5 3.5 7.5V18a2 2 0 0 0 2 2h2V10.5L12 13.5z" />
    <path fill="#34A853" d="M20.5 20a2 2 0 0 0 2-2V7.5L12 13.5l8.5 6.5z" />
    <path fill="#FBBC04" d="M20.5 4h-2L12 8.5 5.5 4h-2A2 2 0 0 0 1.5 6v1.5L12 13.5 22.5 7.5V6a2 2 0 0 0-2-2z" />
    <path fill="#4285F4" d="M16.5 20V10.5L12 13.5l-4.5-3V20z" />
  </svg>
);

/* ===== Styles (same look) ===== */
function Style() {
  return (
    <style>{`
:root{
  --text:#111827; --muted:#6b7280; --line:#e5e7eb; --card:#fff;
  --blue:#3b82f6; --red:#ef4444;
}
*{box-sizing:border-box}
body,#root{background:#fff;}
.ga-wrap{
  font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;
  color:var(--text); max-width:1200px; margin:24px auto; padding:0 24px;
}

h1{margin:0 0 4px; font-size:28px; font-weight:700;}
.ga-muted{color:var(--muted); font-size:14px; margin:0;}
.ga-top{display:flex; align-items:flex-end; justify-content:space-between; gap:16px; padding-bottom:12px; border-bottom:1px solid var(--line); margin-bottom:16px;}
.ga-add{background:var(--blue); color:#fff; text-decoration:none; padding:10px 16px; border-radius:10px; font-weight:700;}
.ga-add:hover{filter:brightness(.96);}

.ga-list{display:flex; flex-direction:column; gap:16px; margin-top:8px;}
.ga-card{display:flex; align-items:center; justify-content:space-between; gap:16px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 20px; box-shadow:0 6px 18px rgba(0,0,0,.06);}
.ga-skeleton{height:88px; background:linear-gradient(90deg,#f3f4f6 25%, #eceff3 50%, #f3f4f6 75%); background-size:400% 100%; animation:shine 1.1s infinite;}
@keyframes shine {0%{background-position:200% 0} 100%{background-position:-200% 0}}
.ga-left{display:flex; gap:14px; align-items:center;}
.ga-gmail{width:36px; height:36px; display:grid; place-items:center; background:#f8fafc; border:1px solid #eef2f7; border-radius:9px;}
.ga-row{display:flex; align-items:center; gap:10px; flex-wrap:wrap;}
.ga-email{font-weight:700; font-size:16px;}
.ga-badge{background:#f3f4f6; color:#374151; padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700;}
.ga-muted{color:var(--muted); font-size:14px; margin-top:2px;}

.ga-actions{display:flex; align-items:center; gap:12px; margin-left:auto;}
.ga-btn{display:inline-flex; align-items:center; gap:8px; height:40px; padding:0 16px; border-radius:10px; border:1px solid var(--line); background:#fff; color:#111827; font-weight:700; cursor:pointer;}
.ga-btn:hover{background:#f9fafb;}
.ga-danger{display:inline-flex; align-items:center; gap:10px; height:40px; padding:0 16px; border-radius:10px; background:var(--red); border:1px solid var(--red); color:#fff; font-weight:800; cursor:pointer;}
.ga-danger:hover{filter:brightness(.95);}
.ga-danger:disabled{opacity:.6; cursor:not-allowed;}
.ga-chip{display:inline-grid; place-items:center; width:28px; height:28px; border-radius:999px; background:rgba(255,255,255,.25);}

.ga-backdrop{position:fixed; inset:0; background:rgba(0,0,0,.25); display:grid; place-items:center; padding:16px; z-index:50;}
.ga-modal{width:100%; max-width:720px; background:#fff; border-radius:16px; border:1px solid var(--line); overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,.15);}
.ga-modal-head{display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid var(--line);}
.ga-x{border:none; background:transparent; font-size:26px; line-height:1; cursor:pointer;}
.ga-modal-body{padding:16px; display:grid; gap:12px;}
.ga-field{display:grid; gap:6px;}
.ga-label{font-weight:700; color:#374151;}
.ga-value{color:#111827;}
.ga-input{border:1px solid var(--line); background:#f9fafb; border-radius:10px; padding:10px 12px;}
.ga-perms{list-style:none; padding:0; margin:0; display:grid; gap:8px;}
.ga-dot{display:inline-block; width:9px; height:9px; background:#22c55e; border-radius:999px; margin-right:8px;}
.ga-modal-foot{padding:16px; border-top:1px solid var(--line);}
.wide{width:100%;}

@media (max-width:720px){
  .ga-card{flex-direction:column; align-items:flex-start;}
  .ga-actions{width:100%; justify-content:flex-end;}
}
    `}</style>
  );
}
