import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Allow LAN/Wi-Fi devices to access the dev server (HMR, hot-reload, etc.).
   * Next.js 16+ blocks cross-origin dev resource requests by default.
   * If you connect from a new IP, add it here and restart the dev server.
   */
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "10.212.16.224",
    "10.32.143.13",
    "172.16.242.15",
    // Add more LAN IPs as needed (run `ipconfig` to find yours)
  ],
};

export default nextConfig;
