// app/opengraph-image.tsx — site-wide default OG image (Next.js App Router, next/og).
// Next.js turns this file into /opengraph-image and adds og:image + twitter:image tags
// automatically for this segment and every child without its own opengraph-image.
import { ImageResponse } from "next/og";

export const alt = "BRAND — tagline";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// ---- edit me ----
const BRAND = "BRAND";
const TAGLINE = "One sentence that says what the site does";
const BG = "#0f172a";
const FG = "#ffffff";
const ACCENT = "#38bdf8";
// -----------------

export default async function Image() {
  // Optional custom font (TTF/OTF, not WOFF2). Put the file next to this one:
  // const font = await fetch(new URL("./Inter-Bold.ttf", import.meta.url)).then((r) => r.arrayBuffer());
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 80,
          background: BG,
          color: FG,
          borderTop: `12px solid ${ACCENT}`,
        }}
      >
        <div style={{ display: "flex", fontSize: 36, color: ACCENT, fontWeight: 700 }}>{BRAND}</div>
        <div style={{ display: "flex", fontSize: 72, fontWeight: 700, lineHeight: 1.15, maxWidth: 1000 }}>
          {TAGLINE}
        </div>
        <div style={{ display: "flex", fontSize: 28, color: "#94a3b8" }}>
          {process.env.NEXT_PUBLIC_SITE_URL?.replace(/^https?:\/\//, "") ?? ""}
        </div>
      </div>
    ),
    {
      ...size,
      // fonts: [{ name: "Inter", data: font, weight: 700, style: "normal" }],
    },
  );
}
