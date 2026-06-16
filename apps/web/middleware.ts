import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/register')

  if (!token && !isAuthPage) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (token && isAuthPage) {
    // Attempt to resolve role from backend using the access token
    try {
      const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
      const resp = await fetch(`${backendUrl}/api/v1/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (resp.ok) {
        const user = await resp.json()
        if (user?.role === 'client') {
          return NextResponse.redirect(new URL('/client/dashboard', request.url))
        }
      }
    } catch (err) {
      // ignore and fallback to developer dashboard
      console.warn('middleware: failed to fetch user role', err)
    }

    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
