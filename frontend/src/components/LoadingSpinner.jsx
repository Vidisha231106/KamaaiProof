function LoadingSpinner({ label = "Loading" }) {
  return (
    <div className="loading-inline" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export default LoadingSpinner;
