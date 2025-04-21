import MainLayout from "@/components/MainLayout";
import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Jubilee eKYC Portal",
    description: "Monitor and review the outcomes of eKYC backend processing",
};

export default async function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`antialiased`}>
                <MainLayout>{children}</MainLayout>
            </body>
        </html>
    );
}
