import { NavLink } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

function Layout({ children, theme, toggleTheme }) {
  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="brand-area">
          <div className="brand-mark" aria-hidden="true">
            KP
          </div>
          <div>
            <p className="brand-title">KamaaiProof</p>
            <p className="brand-subtitle">Work Passport for India's Invisible Workforce</p>
          </div>
        </div>

        <nav className="site-nav" aria-label="Main navigation">
          <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/">
            Landing
          </NavLink>
          <NavLink
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            to="/upload"
          >
            Upload
          </NavLink>
          <NavLink
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            to="/result"
          >
            Result
          </NavLink>
        </nav>

        <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
      </header>

      <main className="page-content">{children}</main>
    </div>
  );
}

export default Layout;
