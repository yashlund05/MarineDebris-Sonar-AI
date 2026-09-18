import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#F2EFE7",
          surface: "#FFFCF6",
          elevated: "#E7ECE8",
          subtle: "#D7D6CC",
        },
        border: {
          subtle: "#D7D6CC",
          default: "#B9C5C1",
          strong: "#728985",
        },
        text: {
          primary: "#19313A",
          secondary: "#4F696B",
          muted: "#718384",
        },
        accent: {
          DEFAULT: "#C8523B",
          hover: "#AA4332",
          subtle: "#F7E1DA",
        },
        sonar: {
          navy: "#0F172A",
          teal: "#0D9488",
          sky: "#0284C7",
          amber: "#D97706",
          emerald: "#16A34A",
          rose: "#DC2626",
          slate: "#64748B",
        },
        detection: {
          gear: "#D97706",
          debris: "#DC2626",
          wreck: "#7C3AED",
          pipe: "#0891B2",
          other: "#16A34A",
          natural: "#475569",
          filtered: "#64748B",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "SF Mono", "Roboto Mono", "monospace"],
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
        card: "0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.06)",
        dropdown: "0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.08)",
        modal: "0 20px 25px -5px rgba(15, 23, 42, 0.12), 0 8px 10px -6px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
