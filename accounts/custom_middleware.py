from typing import Any
from django.urls import reverse
from django.http import HttpResponse
# from django.shortcuts import redirect


# class NotActiveUserMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if request.user.is_authenticated:
#             if request.user.is_active == False:
#                 HttpResponse('اکانت شما غیر فعال است .')    
#         response = self.get_response(request)
#         return response


# https://zzzcode.ai/answer-question?id=361f134c-ecc5-4e97-8c1e-763b0cbe9d79