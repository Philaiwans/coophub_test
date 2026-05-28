from myapp.models import CoopPost

class AutoExpireMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Auto-expire approved posts older than 3 months
        try:
            CoopPost.auto_expire_posts()
        except Exception:
            # Prevent blocking requests if DB tables aren't created yet or other issues occur
            pass
        response = self.get_response(request)
        return response
