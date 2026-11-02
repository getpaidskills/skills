// src/pages/og/[...slug].png.ts — build-time OG images for Astro.
// npm i satori @resvg/resvg-js
// Then in your layout: <meta property="og:image" content={new URL(`/og/${slug}.png`, Astro.site)} />
import type { APIRoute, GetStaticPaths } from "astro";
import { getCollection } from "astro:content";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import fs from "node:fs/promises";

// TTF/OTF only (satori does not read WOFF2). Use a CJK font for Chinese titles.
const fontData = await fs.readFile(new URL("../../assets/fonts/Inter-Bold.ttf", import.meta.url));

export const getStaticPaths: GetStaticPaths = async () => {
  // Adapt: one entry per page that needs an image. "index" is the home page.
  const posts = await getCollection("blog");
  return [
    { params: { slug: "index" }, props: { title: "BRAND", subtitle: "Tagline" } },
    ...posts.map((p) => ({ params: { slug: `blog/${p.id}` }, props: { title: p.data.title, subtitle: p.data.description ?? "" } })),
  ];
};

export const GET: APIRoute = async ({ props }) => {
  const { title, subtitle } = props as { title: string; subtitle: string };
  const svg = await satori(
    {
      type: "div",
      props: {
        style: { width: 1200, height: 630, display: "flex", flexDirection: "column", justifyContent: "center", padding: 80, background: "#0f172a", color: "#fff", fontFamily: "Inter" },
        children: [
          { type: "div", props: { style: { fontSize: 30, color: "#38bdf8", marginBottom: 24 }, children: "BRAND" } },
          { type: "div", props: { style: { fontSize: 68, fontWeight: 700, lineHeight: 1.15 }, children: title } },
          subtitle ? { type: "div", props: { style: { fontSize: 30, color: "#94a3b8", marginTop: 24 }, children: subtitle } } : null,
        ].filter(Boolean),
      },
    } as any,
    { width: 1200, height: 630, fonts: [{ name: "Inter", data: fontData, weight: 700, style: "normal" }] },
  );
  const png = new Resvg(svg, { fitTo: { mode: "width", value: 1200 } }).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png" } });
};
