from PIL import Image
import os
import functools
import numpy as np


def open_image(path):
    with Image.open(path) as im:
        im.load()
        if im.mode != "RGB":
            im = im.convert("RGB")
        return im


class MainPhoto:

    def __init__(self, path):
        self.path = path
        self.image = open_image(path)
        self.simplified = False
        print(f"Main photo loaded sucesfully: {self.path}")
        self.show_parameters()

    def show_parameters(self):
        self.width, self.height = self.image.size
        self.ratio = self.width / self.height
        print(f"H: {self.height}  W: {self.width}  H/W Ratio: {self.ratio}")

    def simplify(self, scale):
        self.image = self.image.convert("P", colors=16)
        self.simplified = True
        print(f"Main photo colors simplified!")
        self.image = self.image.resize(
            (round(self.height / scale), round(self.width / scale))
        )
        print("Main photo resized!")
        self.show_parameters()

    def save_image(self):
        if self.image.mode != "RGB":
            print(f"Main image mode: {self.image.mode}, converting to RGB")
            self.image = self.image.convert("RGB")
        self.image.save("mainphoto_simplified.jpg")

    def pixels2list(self):
        self.image = self.image.convert("RGB")
        self.pixel_list = list(self.image.getdata())

    def find_match(self, lib_index):
        matches = []
        for pixel in self.pixel_list:
            differences = {}
            for tile in lib_index:
                difference = self.calculate_color_diff(pixel, tuple(tile.main_color))
                differences.update({tile.id: difference})
            best_match = min(differences, key=differences.get)
            matches.append(best_match)
        self.matched_tiles = matches

    def create_canvas(self, tile_res=100):
        self.mozaik = Image.new("RGB", (tile_res * self.width, tile_res * self.height))

    def create_mozaik(self, tiles, tile_res=100):
        i = 0
        for y in range(0, self.width):
            for x in range(0, self.height):
                tile = tiles[self.matched_tiles[i]].image

                self.mozaik.paste(
                    tile,
                    (
                        x * tile_res,
                        y * tile_res,
                        (x + 1) * tile_res,
                        (y + 1) * tile_res,
                    ),
                )
                i += 1

    @functools.cache
    def calculate_color_diff(self, color1, color2):
        R1, G1, B1 = color1
        R2, G2, B2 = color2

        difference = (
            0.3 * (R1 - R2) ** 2 + 0.59 * (G1 - G2) ** 2 + 0.11 * (B1 - B2) ** 2
        ) ** 0.5
        return difference


class TilePhoto:
    tile_index = 0

    def __init__(self, path):
        self.id = TilePhoto.tile_index
        TilePhoto.tile_index += 1
        self.path = path
        self.image = open_image(path)
        self.main_color = self.get_main_color()
        self.update_properities()

    def update_properities(self):
        self.width, self.height = self.image.size
        self.ratio = self.height / self.width
        # print(f"{self.path} H:{self.height} w:{self.width}")

    def get_main_color(self):
        simplyfied = self.image.copy()
        simplyfied.convert(colors=16)
        simplyfied.resize((1, 1))
        main_color = simplyfied.getpixel((0, 0))
        return main_color

    def croppsquare(self):
        # Ensure the height and width are updated
        self.update_properities()

        if self.ratio != 1:
            diff = abs(self.height - self.width)
            padding = diff // 2

            if self.width > self.height:
                # Crop the width symmetrically
                left = padding
                right = self.width - padding
                top = 0
                bottom = self.height
            else:
                # Crop the height symmetrically
                left = 0
                right = self.width
                top = padding
                bottom = self.height - padding

            # print(f"Cropping with L:{left}, T:{top}, R:{right}, B:{bottom}")
            self.image = self.image.crop((left, top, right, bottom))
            self.update_properities()  # Update dimensions after cropping

            # print(f"Updated dimensions - H:{self.height}, W:{self.width}")

    def resize(self, newsize):
        self.image = self.image.resize((newsize, newsize))

    def save_tile(self):
        print(f"Save in tiles\{self.id}.jpg")
        tiles_directory = "tiles"
        if not os.path.exists(tiles_directory):
            os.makedirs(tiles_directory)
        self.image.save(os.path.join(tiles_directory, f"{self.id}.jpg"))


class TileLib:

    def __init__(self, path):
        self.item_list = self.create_item_list(path)
        self.tiles = []
        print(f"Found {len(self.item_list)} photos in library!")

    def create_item_list(self, path):
        files = [
            os.path.join(path, f)
            for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f))
        ]
        return files

    def create_tiles(self):
        for item in self.item_list:
            tile = TilePhoto(item)
            self.tiles.append(tile)


if __name__ == "__main__":
    mainphoto = MainPhoto("bbb.jpg")
    mainphoto.simplify(10)
    mainphoto.save_image()
    mainphoto.pixels2list()

    lib = TileLib("photo_lib")
    lib.create_tiles()
    for tile in lib.tiles:
        tile.croppsquare()
        tile.resize(100)

    mainphoto.find_match(lib.tiles)
    mainphoto.create_canvas()
    mainphoto.create_mozaik(lib.tiles)
    mainphoto.mozaik.show()
