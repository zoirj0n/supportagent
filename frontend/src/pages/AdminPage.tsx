import { useEffect, useState } from "react";
import { fetchPage } from "../api";
import type { Page } from "../types";

type Meta = { total: number; limit: number; offset: number };
type Account = {
  id: string; gmail_address: string; is_active: boolean;
  connected_at?: string | null; disconnected_at?: string | null;
  token_expiry?: string | null; google_user_id?: string | null; scopes?: string[] | null;
};
type Order = { id: string; user_email?: string; status?: string; created_at?: string };
type EmailLog = {
  id: number; gmail_account_id: string; gmail_msg_id: string; thread_id?: string | null;
  from_email?: string | null; to_email?: string | null; subject?: string | null; snippet?: string | null;
  received_at?: string | null; category?: string | null; order_id?: string | null; is_handled: boolean; created_at?: string | null;
};
type RefundNF = { id: number; gmail_account_id: string; thread_id?: string | null; email_msg_id?: string | null; provided_text?: string | null; created_at?: string | null; }
type Unhandled = { id: number; gmail_account_id: string; email_msg_id?: string | null; thread_id?: string | null; reason?: string | null; importance?: string | null; created_at?: string | null; }
type RAGDoc = { id: number; title?: string | null; content: string; tags?: string[] | null; created_at?: string | null; }
type RAGChunk = { id: number; doc_id: number; content: string; tags?: string[] | null; chunk_index?: number | null; created_at?: string | null; }

function Pager({ meta, onMore }: { meta: Meta; onMore: () => void }) {
  const more = meta.offset + meta.limit < meta.total;
  if (!more) return null;
  return (
    <div style={{ marginTop: 12 }}>
      <button onClick={onMore}>Load more</button>
      <span style={{ marginLeft: 8, color: "#6b7280" }}>
        Showing {Math.min(meta.offset + meta.limit, meta.total)} / {meta.total}
      </span>
    </div>
  );
}

function usePaged<T>(path: string, params: Record<string, any> = {}) {
  const [page, setPage] = useState<Page<T>>({ items: [], meta: { total: 0, limit: 50, offset: 0 } });
  const [loading, setLoading] = useState(false);

  async function load(reset = true) {
    setLoading(true);
    try {
      const res = await fetchPage<T>(path, { ...params, limit: page.meta.limit, offset: reset ? 0 : page.meta.offset });
      setPage(res);
    } finally { setLoading(false); }
  }

  async function more() {
    if (page.meta.offset + page.meta.limit >= page.meta.total) return;
    const next = await fetchPage<T>(path, { ...params, limit: page.meta.limit, offset: page.meta.offset + page.meta.limit });
    setPage({ items: [...page.items, ...next.items], meta: next.meta });
  }

  return { page, setPage, loading, load, more };
}

export default function AdminPage() {
  const accounts = usePaged<Account>("/admin/accounts");
  const orders = usePaged<Order>("/admin/orders");
  const logs = usePaged<EmailLog>("/admin/email-logs");
  const refunds = usePaged<RefundNF>("/admin/refund-not-found");
  const unhandled = usePaged<Unhandled>("/admin/unhandled-emails");
  const docs = usePaged<RAGDoc>("/admin/rag/documents");
  const chunks = usePaged<RAGChunk>("/admin/rag/chunks");

  useEffect(() => {
    accounts.load(); orders.load(); logs.load();
    refunds.load(); unhandled.load(); docs.load(); chunks.load();
  }, []);

  return (
    <div style={{ padding: 16, fontFamily: "ui-sans-serif, system-ui" }}>
      <h1>Admin Data</h1>
      <p style={{ color: "#6b7280" }}>Browse raw tables exposed by the API.</p>

      <Section title="Accounts" loading={accounts.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>Email</th><th>Active</th><th>Connected</th><th>Disconnected</th><th>Scopes</th></tr></thead>
          <tbody>
            {accounts.page.items.map(a => (
              <tr key={a.id}>
                <td>{a.id}</td>
                <td>{a.gmail_address}</td>
                <td>{String(a.is_active)}</td>
                <td>{a.connected_at ?? ""}</td>
                <td>{a.disconnected_at ?? ""}</td>
                <td>{(a.scopes ?? []).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pager meta={accounts.page.meta} onMore={accounts.more}/>
      </Section>

      <Section title="Orders" loading={orders.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>User Email</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>
            {orders.page.items.map(o => (
              <tr key={o.id}><td>{o.id}</td><td>{o.user_email}</td><td>{o.status}</td><td>{o.created_at}</td></tr>
            ))}
          </tbody>
        </table>
        <Pager meta={orders.page.meta} onMore={orders.more}/>
      </Section>

      <Section title="Email Logs" loading={logs.loading}>
        <table className="tbl">
          <thead><tr>
            <th>ID</th><th>Account</th><th>Msg ID</th><th>Thread</th>
            <th>From</th><th>To</th><th>Subject</th><th>Snippet</th>
            <th>Received</th><th>Category</th><th>Order</th><th>Handled</th>
          </tr></thead>
          <tbody>
            {logs.page.items.map(e => (
              <tr key={e.id}>
                <td>{e.id}</td><td>{e.gmail_account_id}</td><td>{e.gmail_msg_id}</td><td>{e.thread_id}</td>
                <td>{e.from_email}</td><td>{e.to_email}</td><td>{e.subject}</td><td>{e.snippet}</td>
                <td>{e.received_at}</td><td>{e.category}</td><td>{e.order_id}</td><td>{String(e.is_handled)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pager meta={logs.page.meta} onMore={logs.more}/>
      </Section>

      <Section title="Refund Requests (Not Found)" loading={refunds.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>Account</th><th>Thread</th><th>Email Msg</th><th>Provided Text</th><th>Created</th></tr></thead>
          <tbody>
            {refunds.page.items.map(r => (
              <tr key={r.id}><td>{r.id}</td><td>{r.gmail_account_id}</td><td>{r.thread_id}</td><td>{r.email_msg_id}</td><td>{r.provided_text}</td><td>{r.created_at}</td></tr>
            ))}
          </tbody>
        </table>
        <Pager meta={refunds.page.meta} onMore={refunds.more}/>
      </Section>

      <Section title="Unhandled Emails" loading={unhandled.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>Account</th><th>Email Msg</th><th>Thread</th><th>Reason</th><th>Importance</th><th>Created</th></tr></thead>
          <tbody>
            {unhandled.page.items.map(u => (
              <tr key={u.id}><td>{u.id}</td><td>{u.gmail_account_id}</td><td>{u.email_msg_id}</td><td>{u.thread_id}</td><td>{u.reason}</td><td>{u.importance}</td><td>{u.created_at}</td></tr>
            ))}
          </tbody>
        </table>
        <Pager meta={unhandled.page.meta} onMore={unhandled.more}/>
      </Section>

      <Section title="RAG Documents" loading={docs.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>Title</th><th>Tags</th><th>Created</th></tr></thead>
          <tbody>
            {docs.page.items.map(d => (
              <tr key={d.id}><td>{d.id}</td><td>{d.title}</td><td>{(d.tags ?? []).join(", ")}</td><td>{d.created_at}</td></tr>
            ))}
          </tbody>
        </table>
        <Pager meta={docs.page.meta} onMore={docs.more}/>
      </Section>

      <Section title="RAG Chunks" loading={chunks.loading}>
        <table className="tbl">
          <thead><tr><th>ID</th><th>Doc ID</th><th>Idx</th><th>Tags</th><th>Created</th><th>Content</th></tr></thead>
          <tbody>
            {chunks.page.items.map(c => (
              <tr key={c.id}><td>{c.id}</td><td>{c.doc_id}</td><td>{c.chunk_index}</td><td>{(c.tags ?? []).join(", ")}</td><td>{c.created_at}</td><td>{c.content.slice(0,120)}…</td></tr>
            ))}
          </tbody>
        </table>
        <Pager meta={chunks.page.meta} onMore={chunks.more}/>
      </Section>

      <style>{`
        .tbl { width:100%; border-collapse:collapse; font-size:14px; }
        .tbl th, .tbl td { border:1px solid #e5e7eb; padding:8px 10px; vertical-align:top; }
        .tbl th { background:#f9fafb; text-align:left; }
        h2 { margin-top:28px; }
      `}</style>
    </div>
  );
}

function Section({ title, loading, children }: { title: string; loading: boolean; children: React.ReactNode }) {
  return (
    <section>
      <h2>{title}</h2>
      {loading ? <div>Loading…</div> : children}
    </section>
  );
}
