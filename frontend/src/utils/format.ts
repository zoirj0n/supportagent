export function formatCardDate(iso?: string | null) {
	if (!iso) return "";
	const d = new Date(iso);
	return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  }

  export function formatModalDate(iso?: string | null) {
	if (!iso) return "Unknown";
	const d = new Date(iso);
	const date = d.toLocaleDateString(undefined, {
	  weekday: "long", year: "numeric", month: "long", day: "numeric",
	});
	const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
	return `${date} at ${time}`;
  }
