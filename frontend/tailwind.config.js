/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",   // Scan all React components in src/
    "./src/components/**/*.{js,ts,jsx,tsx}", // Explicitly include components folder
  ],
  theme: {
    extend: {
      colors: {
        rmz01Primary: "#5d2b88",   // RMZ01 theme color
        rmz01Secondary: "#ff8c42",
        rmz01Background: "#f5f5f5",
      },
      boxShadow: {
        soft: "0 4px 14px rgba(0, 0, 0, 0.08)",
      },
    },
  },
  plugins: [],
}
