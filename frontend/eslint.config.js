const nextConfig = require("eslint-config-next");
const coreWebVitalsConfig = require("eslint-config-next/core-web-vitals");

/** @type {import('eslint').Linter.Config[]} */
module.exports = [
  ...coreWebVitalsConfig,
];
