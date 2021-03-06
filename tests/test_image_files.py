import io
import os

from mock import patch
import pytest

from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.cropper.models import Image
from betty.conf.app import settings as bettysettings


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_png():

    path = os.path.join(TEST_DATA_PATH, "Lenna.png")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("Lenna.png")
    assert image.width == 512
    assert image.height == 512
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated

    # Since this image is 512x512, it shouldn't end up getting changed by the optimization process
    assert os.stat(image.optimized.path).st_size == os.stat(image.source.path).st_size


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_jpeg():

    path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("Sam_Hat1.jpg")
    assert image.width == 3264
    assert image.height == 2448
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated

    source = PILImage.open(image.source.path)
    optimized = PILImage.open(image.optimized.path)

    assert source.quantization == optimized.quantization
    assert JpegImagePlugin.get_sampling(source) == JpegImagePlugin.get_sampling(optimized)


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_jpeg_grayscale():

    path = os.path.join(TEST_DATA_PATH, "Sam_Hat1_gray.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("Sam_Hat1_gray.jpg")
    assert image.width == 3264
    assert image.height == 2448
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated

    source = PILImage.open(image.source.path)
    optimized = PILImage.open(image.optimized.path)

    assert source.mode == 'L'
    assert optimized.mode == 'L'

    assert source.size == (3264, 2448)
    assert optimized.size == (3200, 2400)


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_jpeg_save_quant_error():
    path = os.path.join(TEST_DATA_PATH, "Sam_Hat1.jpg")

    def image_save_quant_error(*args, **kw):
        if 'qtables' in kw:
            raise ValueError("Invalid quantization table")

    with patch.object(PILImage.Image, 'save', side_effect=image_save_quant_error) as mock_save:
        Image.objects.create_from_path(path)

    # First save fails, second save succeeds
    assert mock_save.call_count == 2

    second_call = mock_save.call_args_list[1]
    assert isinstance(second_call[0][0], io.BytesIO)
    assert second_call[1] == {'format': 'JPEG', 'icc_profile': None}


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_jpeg_noext():

    path = os.path.join(TEST_DATA_PATH, "Sam_Hat1_noext")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("Sam_Hat1_noext")
    assert image.width == 3264
    assert image.height == 2448
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated

    source = PILImage.open(image.source.path)
    optimized = PILImage.open(image.optimized.path)

    assert source.quantization == optimized.quantization

    assert JpegImagePlugin.get_sampling(source) == JpegImagePlugin.get_sampling(optimized)


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_huge_jpeg():

    path = os.path.join(TEST_DATA_PATH, "huge.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("huge.jpg")
    assert image.width == 8720
    assert image.height == 8494
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated

    assert image.to_native()["width"] == 3200

    optimized = PILImage.open(image.optimized.path)
    assert optimized.size[0] == bettysettings.BETTY_MAX_WIDTH
    assert os.stat(image.optimized.path).st_size < os.stat(image.source.path).st_size


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_l_mode():

    path = os.path.join(TEST_DATA_PATH, "Header-Just_How.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("Header-Just_How.jpg")
    assert image.width == 1280
    assert image.height == 720
    assert image.jpeg_quality is None
    assert os.path.exists(image.optimized.path)
    assert os.path.exists(image.source.path)
    assert not image.animated


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_fucked_up_quant_tables():

    path = os.path.join(TEST_DATA_PATH, "tumblr.jpg")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.source.path.endswith("tumblr.jpg")
    assert image.width == 1280
    assert image.height == 704


@pytest.mark.django_db
@pytest.mark.usefixtures("clean_image_root")
def test_gif_upload():

    path = os.path.join(TEST_DATA_PATH, "animated.gif")
    image = Image.objects.create_from_path(path)

    # Re-load the image, now that the task is done
    image = Image.objects.get(id=image.id)

    assert image.width == 256
    assert image.height == 256
    assert os.path.exists(image.path())
    assert os.path.exists(image.source.path)
    assert os.path.basename(image.source.path) == "animated.gif"
    assert image.animated

    # mparent(2016-03-18): These are now created on demand
    assert not os.path.exists(os.path.join(image.path(), "animated/original.gif"))
    assert not os.path.exists(os.path.join(image.path(), "animated/original.jpg"))
