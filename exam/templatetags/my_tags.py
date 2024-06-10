from django import template
# from config.settings import LANGUAGE_CODE

register = template.Library()

@register.filter(name='e2fnum')
def english_numbers_convertor(number):

    arabic = '۰۱۲۳۴۵۶۷۸۹'
    english = '0123456789'

    translation_table = str.maketrans(english, arabic)
    number = str(number).translate(translation_table)
    return number

@register.filter
def minus_index(my_list,index):
    try:
        value = my_list[-index]
        return str(value)
    except IndexError:
        return False

@register.filter
def minus_index_int(my_list,index):
    try:
        value = my_list[-index]
        return int(value)
    except IndexError:
        return False

@register.filter
def like_filter(like_dislike_list, bool):
    if bool:
        like_dislike_count = like_dislike_list.filter(like=True)
    else:
        like_dislike_count = like_dislike_list.filter(like=False)
    
    return like_dislike_count.count()

    
