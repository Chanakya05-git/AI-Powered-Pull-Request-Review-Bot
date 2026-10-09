import json


def load_profile(path):
    d = open(path).read()
    x = json.loads(d)
    return x["user"]["email"]