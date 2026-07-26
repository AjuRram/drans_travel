/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.DEPLOY_STATIC_EXPORT === "true" ? "export" : "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
