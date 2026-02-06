"use client";
import { Toaster, ToastBar } from "react-hot-toast";

export default function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      gutter={12}
      containerStyle={{ top: 20, right: 20 }}
      toastOptions={{
        duration: 4000,
        style: {
          fontSize: "0.875rem",
          maxWidth: "420px",
          padding: "14px 18px",
          borderRadius: "14px",
          background: "#141414",
          color: "#E5E5E5",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow:
            "0 16px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.03)",
          backdropFilter: "blur(16px)",
          fontWeight: "500",
          lineHeight: "1.5",
        },
        success: {
          style: {
            background: "#0f1f17",
            border: "1px solid rgba(16,185,129,0.2)",
            color: "#d1fae5",
          },
          iconTheme: {
            primary: "#10B981",
            secondary: "#0A0A0A",
          },
        },
        error: {
          style: {
            background: "#1f0f0f",
            border: "1px solid rgba(239,68,68,0.2)",
            color: "#fecaca",
          },
          iconTheme: {
            primary: "#EF4444",
            secondary: "#0A0A0A",
          },
        },
      }}
    >
      {(t) => (
        <ToastBar
          toast={t}
          style={{
            ...t.style,
            animation: t.visible
              ? "toast-enter 0.35s cubic-bezier(0.21,1.02,0.73,1)"
              : "toast-exit 0.4s forwards cubic-bezier(0.06,0.71,0.55,1)",
          }}
        />
      )}
    </Toaster>
  );
}
