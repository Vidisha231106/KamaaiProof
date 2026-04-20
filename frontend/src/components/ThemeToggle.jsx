function ThemeToggle({ theme, toggleTheme }) {
  const isLight = theme === "light";

  return (
    <button
      className="theme-toggle"
      onClick={toggleTheme}
      type="button"
      aria-label={`Switch to ${isLight ? "dark" : "light"} mode`}
      aria-pressed={!isLight}
      title={`Switch to ${isLight ? "dark" : "light"} mode`}
    >
      <span className="theme-toggle-track" aria-hidden="true" />
      <span className={`theme-toggle-knob ${isLight ? "right" : "left"}`} aria-hidden="true" />
      <span className="theme-toggle-label">{isLight ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}

export default ThemeToggle;
