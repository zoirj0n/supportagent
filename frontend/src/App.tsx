import { NavLink, Routes, Route } from "react-router-dom";
import AccountsPage from "./pages/AccountsPage";
import AdminPage from "./pages/AdminPage";

export default function App() {
  return (
    <>
      <TopNav />
      <Routes>
        <Route path="/" element={<AccountsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

function TopNav() {
  return (
    <nav style={{
      display:"flex", gap:12, alignItems:"center",
      borderBottom:"1px solid #e5e7eb", padding:"10px 16px",
      fontFamily:"ui-sans-serif, system-ui"
    }}>
      <strong>Support Agent</strong>
      <NavLink to="/" style={({isActive})=>({ textDecoration: isActive ? "underline":"none" })}>
        Accounts
      </NavLink>
      <NavLink to="/admin" style={({isActive})=>({ textDecoration: isActive ? "underline":"none" })}>
        Admin
      </NavLink>
    </nav>
  );
}

function NotFound() {
  return (
    <div style={{ padding:16, fontFamily:"ui-sans-serif, system-ui" }}>
      <h2>Page not found</h2>
      <p>Try <a href="/">Accounts</a> or <a href="/admin">Admin</a>.</p>
    </div>
  );
}
