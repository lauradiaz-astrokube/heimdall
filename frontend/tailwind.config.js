/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Fondos dark
        void:    "#05080f",
        asgard:  "#080d1c",
        card:    "#0c1220",
        cardHov: "#101828",
        // Bordes dark
        rim:     "#1a2540",
        rimGold: "#c9a84b33",
        // Acento nórdico
        gold:    "#c9a84b",
        goldL:   "#e8c96d",
        // Bifrost
        bifrost: "#6d28d9",
        frost:   "#38bdf8",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "bifrost": "linear-gradient(135deg, #3b82f6 0%, #7c3aed 40%, #c9a84b 100%)",
        "bifrost-h": "linear-gradient(90deg, #3b82f6 0%, #7c3aed 50%, #c9a84b 100%)",
      },
    },
  },
  plugins: [],
};
