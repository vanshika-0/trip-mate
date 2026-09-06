import "./globals.css";

export const metadata = {
  title: "TripMate AI — Multi-Agent Travel Planner",
  description:
    "Search flights, discover hotels, and generate a complete travel itinerary using a multi-agent LangGraph system.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
