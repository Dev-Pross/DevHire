import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/api/:path*', // The URL your frontend calls (e.g. /api/users)
        destination: 'http://13.232.102.49:8000/:path*', // Your AWS HTTP IP (e.g. http://54.12.3.4/users)
      },
    ]
  },
};

export default nextConfig;
