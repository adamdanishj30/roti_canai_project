/**
 * Cloudflare Pages middleware.
 * The repo root is published as the website, so the backend source, the
 * archive, the docs and the AI guides would otherwise be public downloads.
 * _routes.json sends only those paths (plus /api/*) through Functions, so
 * normal page and image requests never run this code.
 */
const BLOCKED = [
  /^\/backend(\/|$)/,
  /^\/archive(\/|$)/,
  /^\/docs(\/|$)/,
  /^\/(README|AGENTS|CLAUDE)\.md$/i,
  /^\/(_headers|_routes\.json|\.gitignore)$/,
];

export async function onRequest({ request, next }) {
  const path = new URL(request.url).pathname;
  if (BLOCKED.some((re) => re.test(path))) {
    return new Response("Not found", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8", "X-Robots-Tag": "noindex" },
    });
  }
  return next();
}
