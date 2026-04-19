function ThemeToggle({ theme, toggleTheme }) {
  const isLight = theme === "light";

  return (
    <button className="theme-toggle" onClick={toggleTheme} type="button" aria-label="Toggle theme">
      <span className="theme-toggle-track" />
      <span className={`theme-toggle-knob ${isLight ? "right" : "left"}`} />
      <span className="theme-toggle-label">{isLight ? "White / Navy" : "Black / White"}</span>
    </button>
  );
}

export default ThemeToggle;
