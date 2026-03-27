import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals.js";
import nextTs from "eslint-config-next/typescript.js";

// eslint-config-next 15.3.8 may export a single config object or an array.
// Normalize to array to prevent "not iterable" errors.
const vitals = Array.isArray(nextVitals) ? nextVitals : [nextVitals];
const ts = Array.isArray(nextTs) ? nextTs : [nextTs];

const eslintConfig = defineConfig([
  ...vitals,
  ...ts,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
