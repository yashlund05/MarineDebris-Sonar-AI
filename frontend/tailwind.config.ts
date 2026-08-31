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
          primary: "#0A0E14",
          surface: "#131820",
          elevated: "#1C2433",
        },
        border: {
          subtle: "#2A3547",
        },
        text: {
          primary: "#E8EDF5",
          secondary: "#8A96A8",
          muted: "#515D6E",
        },
        accent: {
          DEFAULT: "#3B82F6",
          hover: "#2563EB",
        },
        detection: {
          gear: "#F59E0B",
          debris: "#EF4444",
          wreck: "#8B5CF6",
          pipe: "#06B6D4",
          other: "#84CC16",
          natural: "#6B7280",
          filtered: "#374151",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
