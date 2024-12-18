import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";
import { viteSingleFile } from "vite-plugin-singlefile";

// https://vitejs.dev/config/
export default defineConfig({
  base: "", // Use relative paths (important if the built app does not include a server)
  plugins: [
    svgr(),
    react(),
    // viteSingleFile({ removeViteModuleLoader: true, inlinePattern: /\.(js|css)$/ })
    viteSingleFile()
  ],
  server: {
    host: "localhost",
    port: 5175,
    open: false,
    // fs:{
    //   allow: ['../../..'],
    //   base: ['/']
    // },
    // watch: {
    //   usePolling: true,
    //   disableGlobbing: false,
    // },
  },
  // Set the root directory to 'reactUi' insted of default 'src'
  // root: 'reactUi',
  // consider changing the build dir
  build: {
    outDir: "ui_bundle", // Adjust the output directory if needed
  },
});
