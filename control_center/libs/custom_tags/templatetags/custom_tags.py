from django.template.defaulttags import register


@register.filter()
def get(array, item):
    try:
        return array[item]
    except:
        return None
