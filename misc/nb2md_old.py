import argparse
from nbdev.export2html import _nbdev_detach, convert_md
import os
import re

CURRENT_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
SITE_ROOT = os.path.abspath(os.path.join(CURRENT_FILE, ".."))
MARKDOWN_PATH = os.path.abspath(os.path.join(SITE_ROOT, "_posts/notebook_posts"))


def nbdev_nb2md(
    fname:str,  # A notebook file name to convert
    dest:str='.',  # The destination folder
    img_path="",  # Folder to export images to
    jekyll=False  # To use jekyll metadata for your markdown file or not
):
    "Convert the notebook in `fname` to a markdown file"
    if img_path == "":
        #img_path = dest + "/" + nb_name(fname) + "_files"
        img_path = imgpath(fname)
        os.makedirs(img_path, exist_ok=True)
    _nbdev_detach(fname, dest=img_path)
    convert_md(fname, dest, jekyll=jekyll, img_path=img_path)

def touchup_markdown(fname):
    with open(fname, "r") as f:
        txt = f.read()

    # Move metadata to top
    pattern="---\n.*\n---"
    metadata = re.search(pattern, txt, re.DOTALL).group()
    txt = f"{metadata}\n{txt.replace(metadata,'')}"
    
    # TODO: When using $$ ... $$, you need to escape \\ to \\\.
    #       and apparently remove newlines?
    # https://stackoverflow.com/questions/7124778/how-can-i-match-anything-up-until-this-sequence-of-characters-in-a-regular-exp
    pattern=r"\$\$(.+?)\$\$"
    for t in re.findall(pattern, txt, re.DOTALL):
        tt = t.replace("\\\\", "\\\\\\").replace("\n", " ")
        txt = txt.replace(f"$${t}$$", f"$${tt}$$")

    # Escape double dollar signs
    txt = txt.replace("$$", r"\$\$")


    # Fix links to be relative
    txt = txt.replace(SITE_ROOT, "")
    txt = txt.replace(f"nb_files/{nb_name(fname)}", f"nb_files/{nb_name(fname)}/")

    # Rewrite
    with open(fname, "w") as f:
        f.write(txt)

def list_notebooks(root_dir):
    notebooks = []
    date_pattern = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-"
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for name in files:
            if name[-6:] == ".ipynb" and ".ipynb_checkpoints" not in root and re.search(date_pattern, name) is not None:
                notebooks.append(os.path.join(root, name))
    return notebooks

def nb_name(fname):
    return "".join(os.path.basename(fname).split('.')[:-1])

def imgpath(fname):
    return os.path.abspath(os.path.join(SITE_ROOT, f"assets/nb_files/{nb_name(fname)}"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run nbdev_nb2md')
    parser.add_argument(
        '--fname',
        type=str,
        default=None
    )
    parser.add_argument(
        '--dest',
        type=str, 
        default=MARKDOWN_PATH
    )
    parser.add_argument("--img_path", type=str, default=None)
    parser.add_argument("--jekyll", action="store_true", default=None)
    parser.add_argument("--all", action="store_true", default=None)
    args_dict = vars(parser.parse_args())
    # No fname means do all
    if args_dict["fname"] is None:
        args_dict["fname"] = os.path.abspath(os.path.join(SITE_ROOT, "src/python"))
        args_dict["all"] = True
    convert_all = args_dict.pop("all")

    nb2md_kwargs = {k: v for k, v in args_dict.items() if v is not None}
    img_path = args_dict["img_path"]
    if not convert_all:
        nbdev_nb2md(**nb2md_kwargs)
        out_fname = os.path.join(
            nb2md_kwargs["dest"],
            "".join(nb_name(nb2md_kwargs["fname"])) + ".md"
        )
        touchup_markdown(out_fname)
    else:
        root_dir = nb2md_kwargs.pop("fname")
        fnames = list_notebooks(root_dir)
        for fname in fnames:
            basename = nb_name(fname)
            out_fname = os.path.join(
                nb2md_kwargs["dest"],
                "".join(basename) + ".md"
            )
            print(f"Converting:\n\t{fname}\nand saving to:\n\t{out_fname}")
            nbdev_nb2md(fname, **nb2md_kwargs)
            touchup_markdown(out_fname)
        

