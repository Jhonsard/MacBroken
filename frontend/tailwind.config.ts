import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          main: "#090E19",
          content: "#030407",
          card: "#070E17",
          input: "#070E17",
          elevated: "#141A26",
        },
        text: {
          primary: "#FFFFFF",
          secondary: "rgba(255,255,255,0.80)",
          muted: "rgba(255,255,255,0.50)",
          dim: "#898F9D",
        },
        accent: {
          DEFAULT: "#1be3ad",
          bright: "#2dffc1",
          dim: "rgba(27,227,173,0.55)",
          turquoise: "#3BFFEF",
        },
        success: "#55ff8a",
        warning: "#f0e050",
        danger: "#FF5555",
        info: "#00B2FF",
        border: {
          subtle: "rgba(180,200,230,0.07)",
          DEFAULT: "rgba(180,200,230,0.16)",
          strong: "rgba(180,200,230,0.28)",
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "Inter", "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "Menlo", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        card: "1rem",
      },
      boxShadow: {
        glow: "0 0 24px rgba(128,255,245,0.20)",
        "glow-strong": "0 0 32px rgba(27,227,173,0.35)",
      },
      keyframes: {
        "msg-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "msg-in": "msg-in 380ms cubic-bezier(0.32, 0.72, 0, 1) both",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
}

export default config