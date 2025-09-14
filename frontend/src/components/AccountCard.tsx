import type { Account } from "../types";
import { formatCardDate } from "../utils/format";
import GmailIcon from "./GmailIcon";

type Props = {
  account: Account;
  primaryId: string | null;
  busyId: string | null;
  onDetails: (id: string) => void;
  onDisconnect: (id: string) => void;
};

export default function AccountCard({ account: a, primaryId, busyId, onDetails, onDisconnect }: Props) {
  return (
    <div className="ga-card">
      <div className="ga-left">
        <div className="ga-gmail"><GmailIcon/></div>
        <div>
          <div className="ga-row">
            <span className="ga-email">{a.gmail_address}</span>
            {(a.is_primary || a.id === primaryId) && <span className="ga-badge">Primary</span>}
          </div>
          <div className="ga-muted">
            {a.is_active
              ? (a.connected_at ? `Connected ${formatCardDate(a.connected_at)}` : "Connected")
              : (a.disconnected_at ? `Disconnected ${formatCardDate(a.disconnected_at)}` : "Disconnected")}
          </div>
        </div>
      </div>

      <div className="ga-actions">
        <button className="ga-btn" onClick={() => onDetails(a.id)}>
          <span>Details</span>
        </button>
        <button
          className="ga-danger"
          disabled={!a.is_active || busyId === a.id}
          onClick={() => onDisconnect(a.id)}
        >
          <span>{busyId === a.id ? "Disconnecting…" : "Disconnect"}</span>
        </button>
      </div>
    </div>
  );
}
