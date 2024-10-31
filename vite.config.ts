import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svgr(), react()],
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
  // build: {
  //   outDir: '../dist', // Adjust the output directory if needed
  // },
});
