/* eslint-disable react-hooks/exhaustive-deps */
import { MdErrorOutline, MdWarningAmber, MdInfoOutline, MdClose } from "react-icons/md";

const VARIANTS = {
  error: {
    bg: "#fef2f2",
    border: "#fecaca",
    color: "#991b1b",
    Icon: MdErrorOutline,
  },
  warning: {
    bg: "#fffbeb",
    border: "#fde68a",
    color: "#92400e",
    Icon: MdWarningAmber,
  },
  info: {
    bg: "#eff6ff",
    border: "#bfdbfe",
    color: "#1e40af",
    Icon: MdInfoOutline,
  },
};

function ErrorBanner({ message, onClose, type = "error" }) {
  if (!message) return null;

  const { bg, border, color, Icon } = VARIANTS[type] ?? VARIANTS.error;

  return (
    <div style={{
      width: "100%",
      background: bg,
      borderBottom: `1px solid ${border}`,
      color,
      padding: "11px 32px",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      fontSize: "13.5px",
      fontWeight: 500,
      flexShrink: 0,
      animation: "bannerSlideDown 0.22s ease",
    }}>
      <Icon size={17} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1 }}>{message}</span>
      <button
        onClick={onClose}
        style={{
          background: "none",
          border: "none",
          color,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          padding: "2px 4px",
          opacity: 0.65,
          flexShrink: 0,
        }}
      >
        <MdClose size={17} />
      </button>
    </div>
  );
}

export default ErrorBanner;