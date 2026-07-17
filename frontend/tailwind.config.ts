import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        muted: "var(--color-muted)",
        paper: "var(--color-paper)",
        panel: "var(--color-panel)",
        line: "var(--color-line)",
        brand: "var(--color-brand)",
        "brand-deep": "var(--color-brand-deep)",
        wood: "var(--color-wood)",
        bamboo: "var(--color-bamboo)",
        cinnabar: "var(--color-cinnabar)",
        amber: "var(--color-amber)",
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        danger: "var(--color-danger)",
        info: "var(--color-info)"
      },
      fontFamily: {
        sans: [
          "Noto Sans TC",
          "Inter",
          "Microsoft JhengHei",
          "PingFang TC",
          "system-ui",
          "sans-serif"
        ],
        serif: ["Noto Serif TC", "Songti TC", "PMingLiU", "serif"]
      },
      boxShadow: {
        soft: "0 18px 45px rgba(42, 34, 24, 0.08)",
        insetline: "inset 0 0 0 1px rgba(112, 91, 64, 0.12)"
      },
      backgroundImage: {
        paper:
          "radial-gradient(circle at 18% 12%, rgba(198, 171, 116, 0.14), transparent 26%), radial-gradient(circle at 82% 4%, rgba(43, 94, 76, 0.12), transparent 24%), linear-gradient(135deg, rgba(255,255,255,0.58), rgba(245,239,226,0.82))"
      }
    }
  },
  plugins: []
};

export default config;
