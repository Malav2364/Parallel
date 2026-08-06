PUBLIC_ROUTES = {
    "identity": {
        ("POST", "auth/login"),
        ("POST", "auth/register"),
        ("GET", "auth/verify-email"),
        ("POST", "auth/resend-verification"),
        ("POST", "auth/forgot-password"),
        ("POST", "auth/reset-password"),
        ("POST", "auth/refresh"),
    },
}
