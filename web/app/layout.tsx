import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "MarketRegime", description: "Market regime intelligence and historical trading simulation." };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

