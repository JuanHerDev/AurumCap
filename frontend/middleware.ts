import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const token = req.cookies.get("access_token")?.value;

  // Private routes
  const privateRoutes = ["/dashboard", "/portfolio", "/investments", "/profile", "settings"];

  const isPrivate = privateRoutes.some((path) =>
    req.nextUrl.pathname.startsWith(path)
  );

  if (isPrivate && !token) {
    const loginUrl = new URL("/login", req.url);
    return NextResponse.redirect(loginUrl);
  }

  if (token && (req.nextUrl.pathname === "/login" || req.nextUrl.pathname === "/register")) {
    const dashboardUrl = new URL("/dashboard", req.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/portfolio/:path*", "/login", "/register"],
};
