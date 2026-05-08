import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // Pre-bundle @react-pdf/renderer and its entire dep tree via esbuild.
    // esbuild handles CJS circular dependencies correctly (unlike per-file
    // CJS→ESM transforms). A canvas stub prevents pdfkit from crashing
    // during pre-bundling since canvas is a Node-only optional dep.
    include: ["@react-pdf/renderer"],
    esbuildOptions: {
      plugins: [
        {
          name: "stub-canvas",
          setup(build) {
            build.onResolve({ filter: /^canvas$/ }, () => ({
              path: "canvas",
              namespace: "stub-canvas",
            }));
            build.onLoad({ filter: /.*/, namespace: "stub-canvas" }, () => ({
              contents: "module.exports = {};",
            }));
          },
        },
      ],
    },
  },
});


