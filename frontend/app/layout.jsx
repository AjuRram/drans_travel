import "./globals.css";

export const metadata = {
  title: "VoyageAI — Business travel, intelligently managed",
  description: "B2B corporate travel requests, booking, billing and reporting.",
};

export const viewport = {
  themeColor: "#07182c",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
