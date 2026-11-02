# Fixes for Next.js App Router

All files go in `app/` (or `src/app/`). Use one site URL constant:
```ts
// lib/site.ts
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
```

## Metadata defaults — `app/layout.tsx`
```ts
import type { Metadata, Viewport } from "next";
import { SITE_URL } from "@/lib/site";
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Brand — what it does", template: "%s | Brand" },
  description: "50–160 characters describing the product.",
  alternates: { canonical: "./" },          // resolves per page against metadataBase
  openGraph: { type: "website", siteName: "Brand" },
  twitter: { card: "summary_large_image" },
};
export const viewport: Viewport = { width: "device-width", initialScale: 1 };
// and <html lang="en"> in the JSX
```
Next.js adds the viewport tag automatically; set `lang` yourself.
Note `alternates.canonical: "./"` gives each page its own canonical; set it explicitly on pages
with query-string variants.

## robots — `app/robots.ts`
```ts
import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/api/", "/account/"] }],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
```

## sitemap — `app/sitemap.ts`
```ts
import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPaths = ["", "/pricing", "/blog"];
  const posts: { slug: string; updatedAt: Date }[] = []; // load from your data source
  return [
    ...staticPaths.map((p) => ({ url: `${SITE_URL}${p}`, lastModified: new Date() })),
    ...posts.map((p) => ({ url: `${SITE_URL}/blog/${p.slug}`, lastModified: p.updatedAt })),
  ];
}
```

## 404 — `app/not-found.tsx`
```tsx
import Link from "next/link";
export default function NotFound() {
  return (<main><h1>Page not found</h1><Link href="/">Go home</Link></main>);
}
```
In dynamic routes call `notFound()` from `next/navigation` when the record doesn't exist —
returning an empty page gives a soft 404 (status 200).
Do **not** add a catch-all `redirect("/")` for unknown paths.

## Icons
Drop files in `app/`: `favicon.ico`, `icon.png` (or `icon.svg`), `apple-icon.png` (180×180).
Next.js emits the `<link>` tags.

## HTTPS redirect
Handled by the host/proxy (Vercel, Cloudflare, nginx/Caddy). For nginx:
`server { listen 80; server_name example.com; return 301 https://$host$request_uri; }`

## Images without alt
`next/image` requires `alt`; for decorative images use `alt=""`.
