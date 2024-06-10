import requests
import random

from datetime import timedelta

from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist



from .models import Profile, VerificationCode

def send_code(request, phone_number, user_code=0):
        valide_code = False
        try:
            user = Profile.objects.get(phone_number=phone_number).user
        except:
            try :
                user = request.user
            except:
                messages.error(
                    request,
                    f"<strong>خطا !</strong> کاربر وارد شده غلط می باشد. دوباره امتحان کنید:"
                )
                return JsonResponse({'error': 'some error'}, status=500)

        if not user_code:
            random_int = random.randint(10000, 99999)

            api_key = "266067-f2c94818b0ec407f9e95a6a91e35e607"
            text = f"کد ورود شما : {random_int}"
            sender = "50004075003351"
            recipient = f"09045250913"
            # print(random_int)"

            url = f"https://api.sms-webservice.com/api/V3/Send?ApiKey={api_key}&Text={text}&Sender={sender}&Recipients={recipient}"

            payload = {}
            headers = {}

            try:
                response = requests.get(url, headers=headers, data=payload)
                response.raise_for_status()
                print(response.text)

            except requests.exceptions.HTTPError as err:
                messages.error(
                    request,
                    f"<strong>خطا !</strong>متاسفانه کد ارسال نشد :"
                )
                print(err)
                return redirect('check_code')

            verificatio_code = VerificationCode.objects.create(
                user=user,
                code=random_int
            )
            print(verificatio_code.code)
                
            return verificatio_code
        else:
            
            
            verificatio_code = VerificationCode.objects.filter(user=user).order_by('-datetime_created')[0]
            time_difference  = timezone.now() - verificatio_code.datetime_created
            if time_difference.total_seconds()  < 120:
                admissible_time = True
            else : 
                admissible_time = False
            try:
                if verificatio_code.code == user_code and admissible_time:
                    print('xxxx----xxxxxx')
                    print(verificatio_code.code)
                    valide_code = True
            except:
                pass
            return valide_code