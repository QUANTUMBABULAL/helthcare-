import "./globals.css";

export const metadata = {
  title: "AI Health Companion",
  description: "Food analysis & travel risk advisor powered by AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
