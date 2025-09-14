import { useEffect, useMemo, useState } from "react";
import { API_BASE, listAccounts, getAccount, disconnectAccount } from "../api";
import type { Account, AccountDetails } from "../types";
import AccountList from "../components/AccountList";
import AccountDetailsModal from "../components/AccountDetailsModal";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [details, setDetails] = useState<AccountDetails | null>(null);

  async function load() {
    setLoading(true);
    try {
      const j = await listAccounts();
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

  async function handleDisconnect(id: string) {
    if (!confirm("Disconnect this Gmail account?")) return;
    setBusy(id);
    try {
      await disconnectAccount(id);
      await load();
      setDetails(d => (d?.id === id ? null : d));
    } finally {
      setBusy(null);
    }
  }

  async function openDetails(id: string) {
    try {
      const j = await getAccount(id);
      setDetails({
        id: j.id,
        gmail_address: j.gmail_address,
        is_active: j.is_active,
        connected_at: j.connected_at ?? null,
        disconnected_at: j.disconnected_at ?? null,
        google_user_id: j.google_user_id ?? null,
        scopes: j.scopes ?? [],
      });
      return;
    } catch {
      const a = accounts.find(x => x.id === id);
      if (a) {
        setDetails({
          id: a.id,
          gmail_address: a.gmail_address,
          is_active: a.is_active,
          connected_at: a.connected_at ?? null,
          disconnected_at: a.disconnected_at ?? null,
          scopes: [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
          ],
        });
      }
    }
  }

  return (
    <div className="ga-wrap">
      <header className="ga-top">
        <div>
          <h1>Gmail Accounts</h1>
          <p className="ga-muted">Manage your connected Gmail accounts</p>
        </div>
        <a className="ga-add" href={`${API_BASE}/auth/google/start`}>+ Add Gmail</a>
      </header>

      {loading ? (
        <div className="ga-card ga-skeleton" />
      ) : (
        <AccountList
          accounts={accounts}
          primaryId={primaryId}
          busyId={busy}
          onDetails={openDetails}
          onDisconnect={handleDisconnect}
        />
      )}

      {details && (
        <AccountDetailsModal
          details={details}
          primaryId={primaryId}
          onClose={() => setDetails(null)}
          onDisconnect={handleDisconnect}
        />
      )}
    </div>
  );
}
