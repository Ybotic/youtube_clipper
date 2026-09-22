import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17171a",
        paper: "#f4f1ea",
        lime: "#c8f36c",
        coral: "#ff6b4a",
      },
      fontFamily: {
        display: ["Arial", "Helvetica", "sans-serif"],
        body: ["Courier New", "monospace"],
      },
      boxShadow: {
        card: "0 20px 60px rgba(23, 23, 26, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
