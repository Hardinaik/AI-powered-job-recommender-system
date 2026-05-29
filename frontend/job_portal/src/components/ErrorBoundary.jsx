import { Component } from "react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // Replace with your logging service if you add one later
    console.error("Uncaught error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "12px",
          fontFamily: "var(--font-body, sans-serif)",
          color: "var(--text-primary, #0f1623)",
          background: "var(--bg, #f0f2f8)",
        }}>
          <h2 style={{ margin: 0, fontSize: "18px" }}>Something went wrong</h2>
          <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted, #9299b0)" }}>
            Please refresh the page. If the problem persists, try logging out and back in.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "9px 22px",
              background: "var(--accent, #3b6ef6)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius-sm, 8px)",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;