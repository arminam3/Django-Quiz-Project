from django.http import HttpResponse



# class IsStaffUserMixin:
#     def dispatch(self, request, *args, **kwargs):
#         user = request.user
#         if user.is_authenticated or user.is_staff:
#             if user.profile.is_quiz_maker:
#                 return super().dispatch(request, *args, **kwargs)
#         return HttpResponse('شما مجاز به دسترسی به این صفحه نیستید ')