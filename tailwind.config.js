/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      colors: {
        ios: {
          primary: "#007AFF",
          secondary: "#5AC8FA",
          success: "#34C759",
          warning: "#FF9500",
          error: "#FF3B30",
          background: "#F5F5F7",
          surface: "#FFFFFF",
          text: "#000000",
          textSecondary: "#86868B",
          divider: "#E5E5E7",
        }
      }
    }
  }
}