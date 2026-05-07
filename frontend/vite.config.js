import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // @react-pdf/renderer v4 is incompatible with Vite's ESM pre-bundler
    // because of its canvas dependency. Excluding it makes Vite serve the
    // package directly without transformation, which resolves the crash.
    exclude: ["@react-pdf/renderer"],
  },
});
