import os
import shutil
import urllib.request
from tempfile import TemporaryDirectory

import pytest
from uiucprescon import ocr

TESSDATA_SOURCE_URL_BASE = "https://raw.githubusercontent.com/tesseract-ocr/tessdata"


def download_data(url, destination):
    with TemporaryDirectory() as download_path:
        base_name = os.path.basename(url)
        destination_file = os.path.join(destination, base_name)

        if os.path.exists(destination_file):
            return

        # if not os.path.exists()
        print("Downloading {}".format(url))
        test_file_path = os.path.join(download_path, base_name)

        urllib.request.urlretrieve(url, filename=test_file_path)
        if not os.path.exists(test_file_path):
            raise FileNotFoundError(
                "Failure to download file from {}".format(url))

        shutil.move(test_file_path, destination)


@pytest.mark.integration
def test_reader_with_data(tessdata_eng, sample_images):
    reader = ocr.Reader(language_code="eng", tesseract_data_path=tessdata_eng)
    test_image = os.path.join(sample_images, "IlliniLore_1944_00000011.tif")

    text = reader.read(test_image)
    assert isinstance(text, str)


@pytest.mark.integration
def test_no_osd_file(tmpdir_factory):
    e = ocr.Engine("")
    version = e.get_version()
    english_data_url = "{}/{}/{}".format(TESSDATA_SOURCE_URL_BASE, "4.0.0", "eng.traineddata")

    tessdata_path = tmpdir_factory.mktemp("no_osd_tessdata", numbered=False)

    if not os.path.exists(tessdata_path):
        os.makedirs(tessdata_path)
    download_data(english_data_url, destination=tessdata_path)
    with pytest.raises(FileNotFoundError):

        reader = ocr.Reader(
            language_code="eng",
            tesseract_data_path=tessdata_path
        )
    shutil.rmtree(tessdata_path)

#
# @pytest.mark.expensive
# def test_download_language_pack():
#     with TemporaryDirectory() as download_path:
#         print(download_path)
#         extract_path = os.path.join(download_path, "extracted")
#
#         if not os.path.exists(extract_path):
#             os.mkdir(extract_path)
#
#         ocr.languages.download_language_pack(
#             "4.0.0",
#             destination=download_path,
#             md5_hash="78d0e9da53d29277c0b28c2dc2ead4f9"
#         )
#         expect_file = os.path.join(download_path, "4.0.0")
#         assert os.path.exists(expect_file)
