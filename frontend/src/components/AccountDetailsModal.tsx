import type { AccountDetails } from "../types";
import { formatModalDate } from "../utils/format";
import { humanizeScope, DEFAULT_SCOPES } from "../utils/scopes";
import GmailIcon from "./GmailIcon";

type Props = {
  details: AccountDetails;
  primaryId: string | null;
  onClose: () => void;
  onDisconnect: (id: string) => void;
};

export default function AccountDetailsModal({ details, primaryId, onClose, onDisconnect }: Props) {
  const scopes = details.scopes && details.scopes.length ? details.scopes : DEFAULT_SCOPES;

  return (
    <div className="ga-backdrop" onClick={onClose}>
      <div className="ga-modal" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="ga-modal-head">
          <div className="ga-left">
            <div className="ga-gmail sm"><GmailIcon/></div>
            <div>
              <div className="ga-row">
                <span className="ga-email">{details.gmail_address}</span>
                {(details.is_primary || details.id === primaryId) && <span className="ga-badge">Primary</span>}
              </div>
              <div className="ga-muted">Account Details</div>
            </div>
          </div>
          <button className="ga-x" onClick={onClose} aria-label="Close">×</button>
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
              {scopes.map(s => (
                <li key={s}><span className="ga-dot" /> {humanizeScope(s)}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="ga-modal-foot">
          <button className="ga-danger wide" disabled={!details.is_active} onClick={() => onDisconnect(details.id)}>
            Disconnect Account
          </button>
        </div>
      </div>
    </div>
  );
}
