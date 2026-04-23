import { MdErrorOutline, MdClose } from "react-icons/md";

function ErrorBanner({ message, onClose }) {
  if (!message) return null;
  return (
    <div style={{
      background: "#fff0f0",
      border: "1px solid #ffcccc",
      color: "#cc0000",
      padding: "12px 16px",
      borderRadius: "8px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "16px",
      fontSize: "14px",
      gap: "12px",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <MdErrorOutline size={18} />
        <span>{message}</span>
      </div>
      <button
        onClick={onClose}
        style={{
          background: "none",
          border: "none",
          color: "#cc0000",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          padding: "0",
        }}
      >
        <MdClose size={18} />
      </button>
    </div>
  );
}

export default ErrorBanner;