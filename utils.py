import numpy


def get_spherical_distance(lat1, lon1, lat2, lon2):
    def rad(x):
        return x * numpy.pi / 180
    R = 6371e3
    fi1 = rad(lat1)
    fi2 = rad(lat2)
    delta_fi = rad(lat2-lat1)
    delta_lambda = rad(lon2-lon1)
    a = (numpy.sin(delta_fi / 2) ** 2) + \
        numpy.cos(fi1) * numpy.cos(fi2) * \
        (numpy.sin(delta_lambda / 2) ** 2)
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1-a))
    return R * c / 1000  # km
