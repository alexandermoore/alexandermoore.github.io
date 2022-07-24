import argparse
from nbdev.export2html import _nbdev_detach, convert_md


def nbdev_nb2md(
    fname:str,  # A notebook file name to convert
    dest:str='.',  # The destination folder
    img_path="",  # Folder to export images to
    jekyll=False  # To use jekyll metadata for your markdown file or not
):
    "Convert the notebook in `fname` to a markdown file"
    _nbdev_detach(fname, dest=img_path)
    convert_md(fname, dest, jekyll=jekyll, img_path=img_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run nbdev_nb2md')
    parser.add_argument('fname', type=str)
    parser.add_argument('--dest', type=str, default=None)
    parser.add_argument("--img_path", type=str, default=None)
    parser.add_argument("--jekyll", action="store_true", default=None)
    args_dict = vars(parser.parse_args())
    nb2md_kwargs = {k: v for k, v in args_dict.items() if v is not None}
    nbdev_nb2md(**nb2md_kwargs)