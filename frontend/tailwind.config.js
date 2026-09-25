/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        parchment: "#f2e6c9", "parchment-dark": "#d8c79f", ink: "#241a10",
        legendary: "#ffb703", rare: "#4aa8ff", cursed: "#c1502e", good: "#7fb069",
        panel: "#1c1424", "panel-border": "#4a2f5c", "sky-top": "#241b3a",
        "sky-mid": "#4a2f5c", "sky-horizon": "#a85a3f", muted: "#a99ab5",
      },
      fontFamily: { pixel: ["Press Start 2P", "monospace"], body: ["VT323", "monospace"] },
    },
  },
  plugins: [],
};
