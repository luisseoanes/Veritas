import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Assets de marca (video hero / imagen de fondo) desde el CDN de WEG.
  images: {
    remotePatterns: [{ protocol: "https", hostname: "static.weg.net" }],
  },
};

export default nextConfig;
