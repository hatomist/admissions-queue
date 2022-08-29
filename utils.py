import math


def get_spherical_distance(lat1, lon1, lat2, lon2):
    def rad(x):
        return x * math.pi / 180
    R = 6371e3
    fi1 = rad(lat1)
    fi2 = rad(lat2)
    delta_fi = rad(lat2-lat1)
    delta_lambda = rad(lon2-lon1)
    a = (math.sin(delta_fi / 2) ** 2) + \
        math.cos(fi1) * math.cos(fi2) * \
        (math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c / 1000  # km
