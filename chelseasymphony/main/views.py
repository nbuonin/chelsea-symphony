from chelseasymphony.main.models import Concert
from django.shortcuts import redirect
from django.views.generic.base import View
from urllib.parse import urlencode
from wagtail.core.models import Page


class NextEventView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        # Get the next concert and 302. If none exists then 302 to the most
        # recent season
        next_concert = Concert.objects.future_concerts().first()
        query_string = urlencode(request.GET)

        if next_concert:
            url = next_concert.get_url(request=request)
            if query_string:
                url = '{}?{}'.format(url, query_string)
            return redirect(url)

        if query_string:
            return redirect('/concerts/?' + query_string)

        return redirect('/concerts/')
