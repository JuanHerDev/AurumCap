import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "@/styles/globals.css";
import { AuthProvider } from "@/features/auth/context/AuthProvider";
import { GoogleOAuthProvider } from "@react-oauth/google";
import Navbar from "@/components/layout/Navbar";
import Layout from "@/components/layout/Layout";


const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AurumCap",
  description: "Conoce cómo se está moviendo tu dinero.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
          <AuthProvider>
            <Layout>
              {children}
            </Layout>
          </AuthProvider>
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}
