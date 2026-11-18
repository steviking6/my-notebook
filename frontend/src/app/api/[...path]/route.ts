// Proxy: browser -> Next.js server (/api/...) -> FastAPI backend.
//
// Why not call the backend directly from the browser?
// - the API key stays on the server (anything in browser code is public);
// - same origin for the browser, so no CORS to configure.
//
// Only known backend routes are forwarded (allowlist), so the key cannot be
// sent anywhere else.

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const APP_API_KEY = process.env.APP_API_KEY ?? "";

const ALLOWED = [
  /^documents$/, // GET list, POST upload
  /^documents\/[0-9a-f]{32}$/, // DELETE
  /^documents\/[0-9a-f]{32}\/chunks$/, // GET preview
  /^ingest$/,
  /^search$/,
  /^ask$/,
];

async function forward(request: Request, ctx: RouteContext<"/api/[...path]">) {
  const path = (await ctx.params).path.join("/");
  if (!ALLOWED.some((pattern) => pattern.test(path))) {
    return Response.json({ detail: "Not found" }, { status: 404 });
  }

  const headers = new Headers({ "X-API-Key": APP_API_KEY });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType); // keeps the multipart boundary

  const hasBody = request.method !== "GET" && request.method !== "DELETE";
  const response = await fetch(`${BACKEND_URL}/${path}`, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : undefined,
  });

  return new Response(response.body, {
    status: response.status,
    headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
  });
}

export { forward as GET, forward as POST, forward as DELETE };
