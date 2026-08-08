// Assumes @eslint/js is a project devDependency (npm i -D @eslint/js) —
// unlike the global fallback config, this does not resolve from a shared
// node_modules elsewhere.
const js = require("@eslint/js");

module.exports = [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
    },
  },
];
