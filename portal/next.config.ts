/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '65mz46ka57.execute-api.eu-west-1.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: '6corkstod4.execute-api.eu-west-1.amazonaws.com',
      },
    ],
  },
};

module.exports = nextConfig;
