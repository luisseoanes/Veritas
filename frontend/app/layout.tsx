import type { Metadata, Viewport } from "next";
import { Roboto, Roboto_Mono } from "next/font/google";

import "./globals.css";

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700", "900"],
  variable: "--font-roboto",
  display: "swap",
});

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-roboto-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Veritas · Asesor de accionamientos WEG",
  description:
    "Asesor comercial neuro-simbólico: el agente no busca productos, resuelve un problema de configuración sobre un grafo de restricciones.",
};

export const viewport: Viewport = {
  themeColor: "#06122e",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${roboto.variable} ${robotoMono.variable}`}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
