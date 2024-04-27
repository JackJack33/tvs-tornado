from pygeodesy.sphericalNvector import LatLon

# NOTE: Lat/Lon order is reversed in the polygon sections of the data (i.e. "POLYGON((Lon Lat Lon Lat))")
# this is reversed in the convertToLatLonPoly() function to tuples of (Lat, Lon)

def isInsideLatLonPoly(p_in, poly_in):
    p = LatLon(p_in[0], p_in[1])
    poly = []
    for poly_point in poly_in:
        poly.append(LatLon(poly_point[0], poly_point[1]))
    return p.isenclosedBy(poly)

#POLYGON(Lon Lat Lon Lat Lon Lat ...)
def convertToLatLonPoly(poly_string_in):
    coords_str = poly_string_in.split("((")[1].split("))")[0]
    coords = coords_str.strip().split()
    lon_lat_pairs = [(float(coords[i+1]), float(coords[i])) for i in range(0, len(coords), 2)]
    return lon_lat_pairs

polystring = "POLYGON((-80.42 24.93 -80.44 24.97 -80.71 24.8 -80.59 24.67 -80.33 24.81 -80.42 24.93))"
poly = convertToLatLonPoly(polystring)
print(poly)
p = (24.93, -80.43) # True
print(isInsideLatLonPoly(p, poly))
p = (24.93, -80.41) # False
print(isInsideLatLonPoly(p, poly))

