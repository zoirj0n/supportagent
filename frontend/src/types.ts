export type Account = {
	id: string;
	gmail_address: string;
	is_active: boolean;
	is_primary?: boolean;
	connected_at?: string | null;
	disconnected_at?: string | null;
  };

  export type AccountDetails = {
	id: string;
	gmail_address: string;
	is_active: boolean;
	is_primary?: boolean;
	connected_at?: string | null;
	disconnected_at?: string | null;
	google_user_id?: string | null;
	scopes?: string[];
  };

  export type PageMeta = { total: number; limit: number; offset: number };
  export type Page<T> = { items: T[]; meta: PageMeta };
