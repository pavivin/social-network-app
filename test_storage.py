from io import BytesIO

from PIL import Image


class Storage:
    @classmethod
    def compress_image(cls):
        with open("data/test.jpg", mode="rb") as f:
            _bytes = f.read()

        foo = Image.open(BytesIO(_bytes))

        # downsize the image with an ANTIALIAS filter (gives the highest quality)
        foo = foo.resize((foo.size), Image.LANCZOS)

        foo.save("data/test_opt.jpg", optimize=True, quality=80)  # The saved downsized image size is 22.9k


Storage.compress_image()
