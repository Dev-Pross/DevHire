import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ToastBar, Toaster } from "react-hot-toast";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HireHawk",
  description: "Job process automation",
  icons:{
    icon: "/logo.jpg"
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
    <Toaster
  toastOptions={{
    position: "top-right",
    style: {
      fontSize: "1.7rem",
      minWidth: "350px",
      // padding: "20px 26px",
      borderRadius: "14px",
      boxShadow: "0 4px 22px 0 rgba(34,197,94,0.15)", // soft green shadow
      border: "none",
    },
    success: {
      style: {
        background: "white",
        color: "#2563eb", // blue-600 for text to pop
        borderBottom: "5px solid #34d399", // underline: green-400
        boxShadow: "0 4px 14px 0 rgba(59,130,246,0.08)", // soft blue
        fontWeight: "600",
        letterSpacing: "0.02em"
      },
    },
    error: {
      style: {
        background: "white",
        color: "#ef4444", // red-500 for error text
        borderBottom: "5px solid #ef4444", // vivid red underline
        boxShadow: "0 4px 14px 0 rgba(239,68,68,0.10)", // soft red
        fontWeight: "600",
        letterSpacing: "0.02em"
      },
    },
    info: {
      style: {
        background: "white",
        color: "#14b8a6", // teal-600 for info
        borderBottom: "5px solid #38bdf8", // sky-400 underline
        boxShadow: "0 2px 10px 0 rgba(16,185,129,0.09)", // soft teal
        fontWeight: "600",
        letterSpacing: "0.02em"
      },
    }
  }}
/>

      </body>
    </html>
  );
}
