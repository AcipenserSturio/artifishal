import cv2, urllib.request, csv, os
from pathlib import Path

data = Path(__file__).parent / "data"

PATH_LEGMAP_MASK = str(data / "mask.png")
PATH_LEGMAP_MAP_1 = str(data / "template_other.png")
PATH_LEGMAP_MAP_2 = str(data / "template_gradient.png")
PATH_LEGMAP_MAP_3 = str(data / "template_control.png")
PATH_LEGMAP_OUTPUT = str(data / "generated_map.png")
PATH_LEGMAP_TEMP = str(data / "temp.csv")

URL_LEGMAP_REGIONS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO6EP4kgqhHWnGiFn4DaoIhwLILZA9Msj7a6zKnj7oxT-Sxk4QotNktSYUdZkEd97HP3Rj2lgYg5eW/pub?gid=18708841&single=true&output=csv"
URL_LEGMAP_MACROREGIONS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO6EP4kgqhHWnGiFn4DaoIhwLILZA9Msj7a6zKnj7oxT-Sxk4QotNktSYUdZkEd97HP3Rj2lgYg5eW/pub?gid=1567615958&single=true&output=csv"
URL_LEGMAP_ADJACENCIES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO6EP4kgqhHWnGiFn4DaoIhwLILZA9Msj7a6zKnj7oxT-Sxk4QotNktSYUdZkEd97HP3Rj2lgYg5eW/pub?gid=254405214&single=true&output=csv"


class Region:
    def __init__(self, name, abbr, pop, left, x, y, macroregion, country_name, country_abbr):
        self.name = name
        self.abbr = abbr
        self.pop = int(pop)
        self.left = int(left)
        self.x = int(x)
        self.y = int(y)
        self.coords = (self.x, self.y)
        self.macroregion = macroregion
        self.country_name = country_name
        self.country_abbr = country_abbr
        self.adj = []
        self.pixels = ()
        self.connected = False
    def controlled(self):
        if self.pop == 0:
            if self.left == 0:
                return "not controlled"
            else:
                return "previously controlled"
        else:
            return "controlled"

class Macroregion:
    def __init__(self, name, pop, colour):
        self.name = name
        self.pop = int(pop)
        self.colour = hex_code_to_colour(colour)
        self.regions = []

def get_csv(url):
    contents = urllib.request.urlopen(url).read().decode('utf-8').replace("\r\n", "\n")
    with open(PATH_LEGMAP_TEMP, "w") as f:
        f.write(contents)
    rows = []
    with open(PATH_LEGMAP_TEMP) as f:
        csvinfo = csv.reader(f, delimiter=',', quotechar='"')
        for row in csvinfo:
            rows.append(row)
        return rows

def bucket_fill(image, mask, coords, colour):
    cv2.floodFill(image, mask, coords, (colour[2], colour[1], colour[0]))

def hex_code_to_colour(hex_code):
    return (int(hex_code[1:3], 16), int(hex_code[3:5], 16), int(hex_code[5:7], 16))

def get_colour(pop):
    colour_scheme = [(252, 254, 202),
                     (191, 232, 162),
                     (122, 197, 169),
                     (81, 177, 175),
                     (52, 162, 180),
                     (41, 140, 177),
                     (33, 124, 175),
                     (32, 108, 170),
                     (32, 92, 161),
                     (32, 78, 154),
                     (32, 66, 148),
                     (32, 56, 142),
                     (32, 48, 139),
                     (32, 41, 135),
                     (32, 34, 131),
                     (32, 29, 129),
                     (28, 26, 116),
                     (26, 23, 109),
                     (23, 22, 101),
                     (20, 21, 94),
                     (18, 19, 86),
                     (15, 17, 79),
                     (12, 15, 72)]
    if pop < len(colour_scheme):
        return colour_scheme[pop]
    else:
        return colour_scheme[-1]

def get_region_data():
    region_csv = get_csv(URL_LEGMAP_REGIONS)
    macroregion_csv = get_csv(URL_LEGMAP_MACROREGIONS)
    adjacency_csv = get_csv(URL_LEGMAP_ADJACENCIES)

    col_regions_macroregion = 0
    col_regions_country_name = 1
    col_regions_country_abbr = 2
    col_regions_name = 3
    col_regions_abbr = 4
    col_regions_population = 5
    col_regions_left = 6
    col_regions_coord_x = 7
    col_regions_coord_y = 8

    col_macroregions_name = 0
    col_macroregions_population = 1
    col_macroregions_hex = 2

    col_adjacencies_abbr_1 = 0
    col_adjacencies_abbr_2 = 3

    regions = []
    macroregions = []
    macroregion_dict = {}
    region_dict = {}
    # Use the information from csv to initialise a list of regions and macroregions.
    # This makes it less wordy to work with!
    for macroregion in macroregion_csv:
        if macroregion[col_macroregions_population] and macroregion[col_macroregions_population].isdigit() and macroregion[col_macroregions_hex]:
            current_macroregion = Macroregion(macroregion[col_macroregions_name],
                                              macroregion[col_macroregions_population],
                                              macroregion[col_macroregions_hex])
            macroregion_dict[current_macroregion.name] = current_macroregion
            macroregions.append(current_macroregion)
    for region in region_csv:
        if region[col_regions_population] and region[col_regions_population].isdigit():
            if region[col_regions_coord_x] and region[col_regions_coord_y]:
                current_region = Region(region[col_regions_name],
                                        region[col_regions_abbr],
                                        region[col_regions_population],
                                        region[col_regions_left],
                                        region[col_regions_coord_x],
                                        region[col_regions_coord_y],
                                        macroregion_dict[region[col_regions_macroregion]],
                                        region[col_regions_country_name],
                                        region[col_regions_country_abbr])
                current_region.macroregion.regions.append(current_region)
                region_dict[current_region.abbr] = current_region
                regions.append(current_region)
    for adjacency in adjacency_csv:
        if adjacency[col_adjacencies_abbr_1] in region_dict.keys() and adjacency[col_adjacencies_abbr_2] in region_dict.keys():
            region_dict[adjacency[col_adjacencies_abbr_1]].adj.append(region_dict[adjacency[col_adjacencies_abbr_2]])
            region_dict[adjacency[col_adjacencies_abbr_2]].adj.append(region_dict[adjacency[col_adjacencies_abbr_1]])

    populate_adjacencies(regions, region_dict["WV"])

    return regions, macroregions

def populate_adjacencies(regions, capital):
    queue = [capital]
    while len(queue) != 0:
        for adj in queue[0].adj:
            if not adj.connected:
                adj.connected = True
                if adj.controlled() == "controlled":
                    queue.append(adj)
        del queue[0]

def populate_pixels(region):
    print(region.name)
    template_path = PATH_LEGMAP_MAP_1
    mask_path = PATH_LEGMAP_MASK
    colour = 49

    leg = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    cv2.floodFill(leg, mask, region.coords, colour)
    pixel_list = []
    for col in range(len(leg)):
        if colour in leg[col]:
            for row in range(len(leg[col])):
                if leg[col][row] == colour:
                    pixel_list.append((row, col))
    region.pixels = set(pixel_list)

def find_centre(x, y):
    template_path = PATH_LEGMAP_MAP_1
    mask_path = PATH_LEGMAP_MASK

    colour = 49

    leg = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    cv2.floodFill(leg, mask, (x, y), colour)
    pixel_list = []
    for col in range(len(leg)):
        if colour in leg[col]:
            for row in range(len(leg[col])):
                if leg[col][row] == colour:
                    pixel_list.append((row, col))

    centre_x, centre_y = map(sum, zip(*pixel_list))
    centre = (round(centre_x/len(pixel_list)), round(centre_y/len(pixel_list)))
    if centre not in pixel_list:
        min_distance = min(map(lambda pixel : (pixel[0]-centre_x/len(pixel_list))**2 + (pixel[1]-centre_y/len(pixel_list))**2, pixel_list))
        for pixel in pixel_list:
            if (pixel[0]-centre_x/len(pixel_list))**2 + (pixel[1]-centre_y/len(pixel_list))**2 == min_distance:
                centre = pixel
    return centre

def verify_centres(macroregion_name = ""):
    regions, macroregions = get_region_data()
    for region in regions:
        if not macroregion_name or region.macroregion.name == macroregion_name:
            centre = find_centre(region.x, region.y)
            if centre != region.coords:
                print(region.name, centre)

def get_adjacent_by_coords(coords):
    return ((coords[0]-1, coords[1]), (coords[0], coords[1]-1), (coords[0], coords[1]+1), (coords[0]+1, coords[1]))
def get_square_by_coords(coords):
    square = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            if not (i == 0 and j == 0):
                square.append((coords[0]+i, coords[1]+j))
    return square

def find_info_on(prompt):
    regions, macroregions = get_region_data()
    for region in regions:
        if prompt == region.abbr:
            return "{0} is the abbreviation for the region called {1}, which is part of {2}.\nFor more info on {2}, try `+f {2}`".format(region.abbr, region.name, region.country_name)
    for a in regions:
        if prompt == a.country_name or prompt == a.country_abbr:
            regionlist = []
            for region in regions:
                if region.country_name == a.country_name:
                    regionlist.append(region)
            if prompt == a.country_abbr:
                reply = "{2} is the abbreviation for {0}, a country consisting of {1} region(s):".format(a.country_name, str(len(regionlist)), a.country_abbr)
            else:
                reply = "{0} is a country (abbreviated {2}) consisting of {1} region(s):".format(a.country_name, str(len(regionlist)), a.country_abbr)
            for region in regionlist:
                reply += "\n{0}: {1}".format(region.abbr, region.name)
            return reply
    for region in regions:
        if prompt in region.name:
            return "{1} is a region of {2}. It is abbreviated as {0}.\nFor more info on {2}, try `+f {2}`".format(region.abbr, region.name, region.country_name)
    return "I couldn't find any info on this."


def find_adjacencies_for_region(main_region, regions):
    template_path = PATH_LEGMAP_MAP_1
    mask_path = PATH_LEGMAP_MASK

    colour = 49
    adj_colour = 80
    boundary_colour = 255

    leg = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    coords_to_region_dict = {}
    for region in regions:
        coords_to_region_dict[region.coords] = region
    #print(main_region.coords, main_region.name)
    cv2.floodFill(leg, mask, main_region.coords, colour)
    for adj in main_region.adj:
        cv2.floodFill(leg, mask, adj.coords, adj_colour)
    pixel_list = []
    for col in range(len(leg)):
        if colour in leg[col]:
            for row in range(len(leg[col])):
                if leg[col][row] == colour:
                    pixel_list.append((row, col))
    expanded_pixel_list = pixel_list.copy()
    #print(len(pixel_list))
    if len(pixel_list) > 100000:
        return

    boundary = set()
    for pixel in expanded_pixel_list:
        adj_pixels = get_adjacent_by_coords(pixel)
        if min(map(lambda x : leg[x[1]][x[0]], adj_pixels)) == 0:
            square_pixels = get_square_by_coords(pixel)
            for a in square_pixels:
                boundary.add(a)
    #print(len(expanded_pixel_list), len(boundary))

    """for pixel in expanded_pixel_list:
        if leg[pixel[1]][pixel[0]] != 0:
            leg[pixel[1]][pixel[0]] = boundary_colour"""
    for pixel in boundary:
        if leg[pixel[1]][pixel[0]] not in (0, colour, adj_colour, 192):
                for adj in regions:
                    if pixel in adj.pixels:
                        if "?" not in main_region.abbr and "?" not in adj.abbr:
                            print(main_region.abbr, adj.abbr, sep = "\t")
                        cv2.floodFill(leg, mask, adj.coords, adj_colour)
                        main_region.adj.append(adj)
                        adj.adj.append(main_region)
                        break
    #cv2.imwrite("testing_adjacencies.png", leg)

def generate_adjacencies_new(macroregion_name = ""):
    regions, macroregions = get_region_data()
    for region in regions:
        if not macroregion_name or region.macroregion.name == macroregion_name:
            populate_pixels(region)
    for region in regions:
        if not macroregion_name or region.macroregion.name == macroregion_name:
            find_adjacencies_for_region(region, regions)


def generate_leg_map(mode):
    if mode == "CONTROL":
        template_path = PATH_LEGMAP_MAP_3
    elif mode == "POPULATION" or mode == "LEFT":
        template_path = PATH_LEGMAP_MAP_2
    else:
        template_path = PATH_LEGMAP_MAP_1
    mask_path = PATH_LEGMAP_MASK
    generated_map_path = PATH_LEGMAP_OUTPUT

    leg = cv2.imread(template_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    regions, macroregions = get_region_data()

    # Do the map bit!
    for region in regions:
        #print(region.name)
        if mode == "POPULATION":
            colour = get_colour(region.pop)
        if mode == "LEFT":
            colour = get_colour(region.left)
        if mode == "MACROREGIONS":
            colour = region.macroregion.colour
        if mode == "CONTROL":
            if region.abbr == "WV":
                colour = (1, 128, 22)
            else:
                if region.connected:
                    if region.controlled() == "controlled":
                        colour = (110, 166, 88)
                    elif region.controlled() == "previously controlled":
                        colour = (219, 68, 55)
                    else:
                        colour = (252, 231, 92)
                else:
                    if region.controlled() == "controlled":
                        colour = (66, 133, 244)
                    elif region.controlled() == "previously controlled":
                        colour = (171, 71, 188)
                    else:
                        colour = (219, 219, 219)
        if mode != "ADJACENCIES":
            bucket_fill(leg, mask, region.coords, colour)

    if mode == "ADJACENCIES":
        for region in regions:
            #print(len(region.adj))
            for adj in region.adj:
                cv2.line(leg, region.coords, adj.coords, (63, 0, 0), 1)
        for region in regions:
            radius = 3
            cv2.circle(leg, (region.x, region.y), radius, (255, 255, 255), -1)
            cv2.circle(leg, (region.x, region.y), radius+1, (0, 0, 0), 2)

    cv2.imwrite(generated_map_path, leg)
    return generated_map_path


