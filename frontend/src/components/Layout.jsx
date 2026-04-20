import { useMemo } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import Dock from "./Dock";

function HomeIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3.75 10.8L12 4.5L20.25 10.8V19.25C20.25 19.8023 19.8023 20.25 19.25 20.25H14.5V14.25H9.5V20.25H4.75C4.19772 20.25 3.75 19.8023 3.75 19.25V10.8Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function UploadIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15.75V4.75M12 4.75L8.25 8.5M12 4.75L15.75 8.5M4.75 13.5V18.5C4.75 19.4665 5.5335 20.25 6.5 20.25H17.5C18.4665 20.25 19.25 19.4665 19.25 18.5V13.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ResultIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4.75 19.25H19.25M7.5 16.25V11.5M12 16.25V8.25M16.5 16.25V5.75"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ThemeModeIcon({ theme, size = 18 }) {
  if (theme === "light") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M14.5 3.6A8.25 8.25 0 1 0 20.4 9.5A6.9 6.9 0 1 1 14.5 3.6Z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M12 2.75V5M12 19V21.25M21.25 12H19M5 12H2.75M18.55 5.45L16.95 7.05M7.05 16.95L5.45 18.55M18.55 18.55L16.95 16.95M7.05 7.05L5.45 5.45"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

function Layout({ children, theme, toggleTheme }) {
  const navigate = useNavigate();
  const location = useLocation();

  const dockItems = useMemo(
    () => [
      {
        icon: <HomeIcon />,
        label: "Home",
        onClick: () => navigate("/"),
        className: location.pathname === "/" ? "is-active" : ""
      },
      {
        icon: <UploadIcon />,
        label: "Upload",
        onClick: () => navigate("/upload"),
        className: location.pathname === "/upload" ? "is-active" : ""
      },
      {
        icon: <ResultIcon />,
        label: "Result",
        onClick: () => navigate("/result"),
        className: location.pathname === "/result" ? "is-active" : ""
      },
      {
        icon: <ThemeModeIcon theme={theme} />,
        label: theme === "light" ? "Dark mode" : "Light mode",
        onClick: toggleTheme
      }
    ],
    [location.pathname, navigate, theme, toggleTheme]
  );

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <NavLink className="brand-area" to="/" aria-label="KamaaiProof home">
          <div className="brand-mark" aria-hidden="true">
            KP
          </div>
          <div>
            <p className="brand-title">KamaaiProof</p>
            <p className="brand-subtitle">Work Passport for India's Invisible Workforce</p>
          </div>
        </NavLink>

        <div className="header-controls">
          <div className="header-dock" aria-label="Primary actions">
            <Dock
              items={dockItems}
              className="dock-panel-inline"
              panelHeight={56}
              baseItemSize={40}
              magnification={52}
              distance={130}
              dockHeight={128}
              spring={{ mass: 0.18, stiffness: 135, damping: 16 }}
              expandOnHover={false}
            />
          </div>
        </div>
      </header>

      <main className="page-content" id="main-content">
        {children}
      </main>
    </div>
  );
}

export default Layout;
