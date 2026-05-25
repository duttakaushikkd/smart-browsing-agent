import typography from "@tailwindcss/typography";
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(255,255,255,0.08), 0 24px 80px rgba(0,0,0,0.55)"
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "0.45", transform: "scale(0.98)" },
          "50%": { opacity: "1", transform: "scale(1)" }
        },
        rise: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        pulseSoft: "pulseSoft 1.2s ease-in-out infinite",
        rise: "rise 0.45s ease-out both"
      }
    }
  },
  plugins: [typography]
};

export default config;
