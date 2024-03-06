from dubletten_tool.models import PersonProxy, Group
from apis_ampel.models import AmpelTemp
from apis_core.apis_metainfo.models import Collection
from time import time


def get_group(vorfin):
    """
    Tiny helper function to get group from a vorfin entry.
    Returns Group object.
    """
    try:
        res = Group.objects.get(vorfin=vorfin)
        return res
    except Exception as e:
        print(
            f"Exception in in get_group: {e} for vorfin {vorfin} ({vorfin.id})")
        return None


def is_dublette(p):
    """
    Tiny helper function to check if Person is a "dublette".
    Returns True or False. 
    TODO: could be updated to also check if there is inconsistent data.
    Like: if a person proxy has status candidate, but is not member in a group.
    Or: if a person proxy is member in several groups.
    Or: if a single is member in a group /several groups.
    """
    try:
        pp = PersonProxy.objects.get(person=p)
        if pp.status == "candidate":
            return True
        
        return False
    except:
        return False


def get_ampel(vorfin):
    if AmpelTemp.objects.filter(temp_entity=vorfin):
        ampel = vorfin.ampel.status
    else:
        ampel = "red"
    return ampel


def update_merging_collections():
    """
    This helper function iterates through all person_proxies and orders each person into the singles or dubletten collection.
    This function can be called in the frontend to update those collections after changes to groups - like removing a member, thus changing it's status.
    These changes need to be reflected in the collections.
    """

    print("update collections called")

    Collection.objects.get(name="Dubletten").delete()
    Collection.objects.get(name="Leopolddaten Singles").delete()

    col_hsv = Collection.objects.get(name="Import HSV full 22-6-21")
    col_hzab = Collection.objects.get(name="Import HZAB full 10-3-21")
    col_acc = Collection.objects.get(name="Import ACCESS full 13-10-21")
    col_new, c = Collection.objects.get_or_create(name="Leopolddaten Singles")
    col_dubl, c = Collection.objects.get_or_create(name="Dubletten")

    def check_if_leopold_single(person):
        if person.status == "single":
            c = person.person.collection.all()
            if col_hsv in c or col_hzab in c:
                person.person.collection.add(col_new)
                person.person.save()

    for pp in PersonProxy.objects.all():
        if pp.status == "candidate":
            pp.person.collection.add(col_dubl)
            pp.person.save()
        else:
            check_if_leopold_single(pp)

    print("update finished")


def function_timer(func):

    def wrapper(*args, **kwargs):
        before = time()
        res = func(*args, **kwargs)
        after = time()
        print(after-before)
        return res

    return wrapper
