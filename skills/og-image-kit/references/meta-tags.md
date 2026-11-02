# Meta tag templates

## Plain HTML (put in <head> of every page)

```html
<title>{{TITLE}} | {{BRAND}}</title>
<meta name="description" content="{{DESCRIPTION}}" />
<link rel="canonical" href="{{URL}}" />
<meta property="og:site_name" content="{{BRAND}}" />
<meta property="og:type" content="website" />            <!-- "article" for blog posts -->
<meta property="og:title" content="{{TITLE}}" />
<meta property="og:description" content="{{DESCRIPTION}}" />
<meta property="og:url" content="{{URL}}" />
<meta property="og:image" content="{{ORIGIN}}/og/{{SLUG}}.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="{{TITLE}}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@{{X_HANDLE}}" />     <!-- optional -->
```

## Next.js App Router (`app/layout.tsx`)

```ts
import type { Metadata } from "next";
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: { default: "BRAND", template: "%s | BRAND" },
  description: "…",
  openGraph: { type: "website", siteName: "BRAND" },
  twitter: { card: "summary_large_image" },
};
```
Per page: `export const metadata = { title: "Pricing", description: "…" }` or
`export async function generateMetadata({ params })`. The `opengraph-image.tsx` file convention
fills `og:image` — do not also set `openGraph.images` for the same segment.

Gotcha: `openGraph` objects are **replaced, not merged** between layout and page. If a page sets
`openGraph: { title }`, it loses `siteName`/`type` from the layout unless you spread them again.

## Astro (`src/layouts/Base.astro`)

```astro
---
const { title, description, slug = "index" } = Astro.props;
const url = new URL(Astro.url.pathname, Astro.site);
const image = new URL(`/og/${slug}.png`, Astro.site);
---
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:url" content={url} />
<meta property="og:image" content={image} />
<meta name="twitter:card" content="summary_large_image" />
```
