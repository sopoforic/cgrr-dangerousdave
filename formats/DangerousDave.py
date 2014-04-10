"""Parses Dangerous Dave files."""
import logging
import struct
import os

import yapsy
from PIL import Image

import utilities
from utilities import File

class DangerousDave(yapsy.IPlugin.IPlugin):
    """Parses Dangerous Dave files."""

    key = "dangerous_dave_a"
    title = "Dangerous Dave"
    developer = "John Romero"
    description = "Dangerous Dave (DOS)"

    identifying_files = [
        File("DAVE.EXE", 76586,  "10ac35dd6bc6314cd5caf08a4ffb4275"),
    ]

    @staticmethod
    def verify(path):
        """Verifies that the provided path is the supported game."""
        return utilities.verify(DangerousDave.identifying_files, path)

    @staticmethod
    def extract_tiles(path):
        """Extract the tiles."""

        tiles = []

        with open(os.path.join(path, "EGADAVE.DAV"), "rb") as data:
            count = struct.unpack_from("I", data.read(4))[0]
            offsets = struct.unpack_from("I" * count, data.read(4*count))
            print(offsets[1])

            for i in range(count):
                if i != count - 1:
                    tiles.append(data.read(offsets[i+1] - offsets[i]))
                else:
                    tiles.append(data.read())
            for i in range(len(tiles)):
                if len(tiles[i]) == 128:
                    tiles[i] = (tiles[i], (16, 16))
                else:
                    num = tiles[i][0]
                    width = tiles[i][0]
                    length = tiles[i][2]
                    tiles[i] = (tiles[i][4:], (width, length))

        return list(filter(None, map(DangerousDave.convert_tile, tiles)))

    @staticmethod
    def convert_tile(tilepack):
        """Convert a tile to a usable format."""

        # This dict maps the EGA palette to RGB.
        ega_colors = {
            0  : (0x00, 0x00, 0x00), # Black
            1  : (0x00, 0x00, 0xAA), # Dark Blue
            2  : (0x00, 0xAA, 0x00), # Dark Green
            3  : (0x00, 0xAA, 0xAA), # Dark Cyan
            4  : (0xAA, 0x00, 0x00), # Dark Red
            5  : (0xAA, 0x00, 0xAA), # Purple
            6  : (0xAA, 0xAA, 0x00), # Brown
            7  : (0xAA, 0xAA, 0xAA), # Grey
            8  : (0x55, 0x55, 0x55), # Dark Grey
            9  : (0x55, 0x55, 0xFF), # Blue
            10 : (0x55, 0xFF, 0x55), # Green
            11 : (0x55, 0xFF, 0xFF), # Cyan
            12 : (0xFF, 0x55, 0x55), # Red
            13 : (0xFF, 0x55, 0xFF), # Pink
            14 : (0xFF, 0xFF, 0x55), # Yellow
            15 : (0xFF, 0xFF, 0xFF), # White
        }

        # This is a bit ugly. I'm passing the tiles in as (data, (width, rows)),
        # and python kept complaining at me. This would be prettier in Haskell!
        tile, realwidth, rows = (tilepack[0], tilepack[1][0], tilepack[1][1])

        # All images are stored in EGADAVE.DAV with widths rounded up to a
        # multiple of 8 (e.g. any image with real width between 9 and 16 pixels
        # is stored as a 16 pixel wide image). 'Padding' pixels are blank.
        #
        # Since the image metadata lists the 'real' cropped size of the image,
        # this function rounds the width up so we can process the data. The
        # image should be cropped later.
        width = int(8 * round((realwidth + 4)/8))

        # Bytes per channel per row.
        row_bytes = width//8

        # There's an extra row of image data on each tile that needs to be
        # thrown away. No idea why.
        if row_bytes * (rows + 1) * 4 == len(tile):
            tile = tile[:-(row_bytes*4)]
        # Not all tiles seem to follow the same format. One of them claims to be
        # 8x1 pixels, but it's really 32x21, according to my highly scientific
        # guess-and-check methodology. It's possible it should be cropped to
        # another size, though.
        elif row_bytes * rows * 4 != len(tile):
            # logging.error("Size mismatch! Expected: {} ({}x{}), Actual: {}".
            #     format(rows * row_bytes * 4, width, rows, len(tile)))
            width += 24
            # set realwidth to width so cropping doesn't fail later
            realwidth = width
            row_bytes += 3
            rows = len(tile)//(4*row_bytes)
            if sum(tile) == 0:
                # The following code will spit out blank images 20 pixels tall
                # for these, but I don't know if that's really right. There's
                # not much point in exporting the blank images, anyway, so I'm
                # commenting it out, and leaving it here for posterity.
                #
                # rows = 20
                # width = 2*len(tile)//rows
                # row_bytes = width//8
                return

        # Create a blank array to hold the image data. These tiles are stored in
        # two pixels per byte.
        image = [0]*(2*len(tile))

        # See doc/DangerousDave.txt for details about the image format.

        # For each actual row in the image
        for i in range(rows):
            # intensity
            b = 0
            # Glue together the bytes for that row as a big number
            for j in range(row_bytes):
                b += (256 ** (row_bytes - 1 - j))*tile[4*row_bytes*i + j]
            # For each bit in that number, if it's on, mark that on the final
            # image. Intensity is bit 4. RGB are bits 3, 2, and 1.
            for bit in range(width, 0, -1):
                if b&(2 ** (bit - 1)) != 0:
                    image[width*(i + 1) - bit] += 8

            # red
            b = 0
            for j in range(row_bytes):
                b += (256 ** (row_bytes - 1 - j))*tile[4*row_bytes*i + j + row_bytes]
            for bit in range(width, 0, -1):
                if b&(2 ** (bit - 1)) != 0:
                    image[width*(i + 1) - bit] += 4

            # green
            b = 0
            for j in range(row_bytes):
                b += (256 ** (row_bytes - 1 - j))*tile[4*row_bytes*i + j + 2*row_bytes]
            for bit in range(width, 0, -1):
                if b&(2 ** (bit - 1)) != 0:
                    image[width*(i + 1) - bit] += 2

            # blue
            b = 0
            for j in range(row_bytes):
                b += (256 ** (row_bytes - 1 - j))*tile[4*row_bytes*i + j + 3*row_bytes]
            for bit in range(width, 0, -1):
                if b&(2 ** (bit - 1)) != 0:
                    image[width*(i + 1) - bit] += 1

        # Convert from the EGA palette to RGB
        image = [ega_colors[pixel] for pixel in image]

        # Put those pixels into an image
        img = Image.new('RGB', (width, rows))
        img.putdata(image)

        # Now crop the image to its real size, in case it had a width that was
        # not a multiple of 8.
        img = img.crop(box=(0, 0, realwidth, rows))
        
        return img
