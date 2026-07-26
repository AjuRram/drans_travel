/** @type {import('next').NextConfig} */

// Build target is chosen per platform:
//   DEPLOY_STATIC_EXPORT=true -> "export"     (static build for the Cloudflare Worker)
//   VERCEL=1                  -> unset        (Vercel builds its own serverless output)
//   otherwise                 -> "standalone" (self-hosted / Docker, see Dockerfile)
//
// Leaving `output` unset on Vercel is deliberate: "standalone" emits a custom
// Node server under .next/standalone for self-hosting, which is not what the
// Vercel builder consumes.
const isStaticExport = process.env.DEPLOY_STATIC_EXPORT === "true";
const isVercel = process.env.VERCEL === "1";

const nextConfig = {
  ...(isStaticExport
    ? { output: "export" }
    : isVercel
      ? {}
      : { output: "standalone" }),
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
