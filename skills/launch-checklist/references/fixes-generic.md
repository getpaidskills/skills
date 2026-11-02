# Fixes for plain HTML / other frameworks

- **Head tags**: put title, description, canonical, viewport, OG in the shared layout/partial.
  Template in `og-image-kit/references/meta-tags.md` if that skill is installed, else:
  `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **robots.txt** (static file at web root):
  ```
  User-agent: *
  Allow: /
  Sitemap: https://example.com/sitemap.xml
  ```
- **sitemap.xml**: most SSGs have a plugin (Astro `@astrojs/sitemap`, Hugo built-in, Jekyll
  `jekyll-sitemap`, VitePress `sitemap.hostname`). Hand-written minimal form:
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/</loc></url>
  </urlset>
  ```
- **404 status**:
  - Static hosts: Netlify/Cloudflare Pages/GitHub Pages serve `404.html` with status 404 automatically.
  - SPA on nginx: `try_files $uri $uri/ /index.html;` makes every path 200. Prefer prerendering
    known routes and `error_page 404 /404.html;` for the rest.
  - Express: final middleware `app.use((req, res) => res.status(404).send(...))`.
- **Astro**: set `site` in `astro.config.mjs`, add `src/pages/404.astro`, `@astrojs/sitemap`.
- **SPA with no SSR** (Vite + React Router): crawlers that don't run JS see an empty shell.
  Options: prerender (vite-plugin-ssg, react-snap) or move marketing pages to SSR/SSG.
