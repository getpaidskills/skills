// app/blog/[slug]/opengraph-image.tsx — one image per dynamic page.
// Replace getPost() with your real data source (MDX frontmatter, CMS, DB...).
import { ImageResponse } from "next/og";
// import { getPost } from "@/lib/posts";

export const alt = "Article preview";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

async function getPost(slug: string): Promise<{ title: string; description?: string } | null> {
  // TODO: replace with your data loader
  return { title: slug.replace(/-/g, " ") };
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params; // Next.js 15+: params is a Promise
  const post = await getPost(slug);
  const title = post?.title ?? "Not found";
  const fontSize = title.length > 60 ? 56 : title.length > 35 ? 64 : 76;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 80,
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          color: "#fff",
        }}
      >
        <div style={{ display: "flex", fontSize: 30, color: "#38bdf8", marginBottom: 24 }}>BRAND · Blog</div>
        <div style={{ display: "flex", fontSize, fontWeight: 700, lineHeight: 1.15 }}>{title}</div>
        {post?.description ? (
          <div style={{ display: "flex", fontSize: 30, color: "#94a3b8", marginTop: 24 }}>
            {post.description.slice(0, 120)}
          </div>
        ) : null}
      </div>
    ),
    size,
  );
}
