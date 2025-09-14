import type { Account } from "../types";
import AccountCard from "./AccountCard";

type Props = {
  accounts: Account[];
  primaryId: string | null;
  busyId: string | null;
  onDetails: (id: string) => void;
  onDisconnect: (id: string) => void;
};

export default function AccountList({ accounts, primaryId, busyId, onDetails, onDisconnect }: Props) {
  return (
    <div className="ga-list">
      {accounts.map(a => (
        <AccountCard
          key={a.id}
          account={a}
          primaryId={primaryId}
          busyId={busyId}
          onDetails={onDetails}
          onDisconnect={onDisconnect}
        />
      ))}
    </div>
  );
}
