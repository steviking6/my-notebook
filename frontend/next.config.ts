import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // minimal server.js + only the needed node_modules (small Docker image)
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
