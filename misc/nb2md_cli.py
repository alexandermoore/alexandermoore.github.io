import argparse
import os
import re
import logging
logging.basicConfig(level=logging.WARNING)
from dataclasses import dataclass
from nb2md import NBExporter, DATE_PATTERN, SITE_ROOT
from datetime import datetime

# key: value  OR key: "value" are extracted as 2 groups: 'key' and 'value'
FRONTMATTER_PATTERN = r'(.*):\s*"{0,1}([^"]*)"{0,1}\s*'
NB_DIR = os.path.abspath(os.path.join(SITE_ROOT, "src/python"))

exporter = NBExporter()

@dataclass
class FrontmatterConfig:
    draft: str = False
    date: str = None
    publish: bool = False

def list_notebooks(root_dir):
    notebooks = []
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for name in files:
            if name[-6:] == ".ipynb" and ".ipynb_checkpoints" not in root: # and re.search(DATE_PATTERN, name) is not None:
                notebooks.append(os.path.join(root, name))
    return notebooks

def convert_notebook(fname):
    def _boolean_value(v, exception_msg):
        v = v.lower()
        if value not in ['true', 'false']:
            raise ValueError(exception_msg)
        return v == 'true'

    cfg = FrontmatterConfig()
    nb_name = NBExporter.nb_name(fname)
    nb = NBExporter.read_notebook(fname)
    # Check frontmatter
    frontmatter = nb.cells[0].get("source", "")
    if frontmatter[:3] != "---":
        print(f"Notebook {fname} does not contain frontmatter! Ignoring...")
        return False

    for line in frontmatter.split('\n'):
        line = line.strip()
        result = re.match(FRONTMATTER_PATTERN, line)
        if result:
            key, value = result.group(1), result.group(2)
            if key == "_draft":
                cfg.draft = _boolean_value(
                    value,
                    f"Invalid draft frontmatter parameter {value} for notebook {fname}")
            if key == "_date":
                value = value.lower().strip()
                if value == "today":
                    value = datetime.today().strftime('%Y-%m-%d')
                if not re.search(DATE_PATTERN, value):
                    raise ValueError(f"Invalid date {value} for notebook {fname}")
                cfg.date = value
            if key == "_publish":
                cfg.publish = _boolean_value(
                    value,
                    f"Invalid `publish` frontmatter parameter {value} for notebook {fname}")

    # Convert notebook
    if not cfg.publish:
        print(f"Ignoring notebook {fname}")
        return False
    exporter.convert_to_markdown(fname, notebook_name=nb_name, date=cfg.date, draft=cfg.draft)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert notebook(s) to markdown')
    parser.add_argument(
        '--fname',
        type=str,
        default=None
    )
    parser.add_argument(
        '--dest',
        type=str, 
        default=None
    )
    # parser.add_argument("--img_path", type=str, default=None)
    # parser.add_argument("--jekyll", action="store_true", default=None)
    # parser.add_argument("--all", action="store_true", default=None)
    #args_dict = vars(parser.parse_args())
    args = parser.parse_args()
    if args.fname:
        nb_fnames = [args.fname]
    else:
        nb_fnames = list_notebooks(NB_DIR)
    print("="*30 + f"\nFound {len(nb_fnames)} notebooks\n" + "="*30)
    num_converted = 0
    for i, fname in enumerate(nb_fnames):
        print("="*3 + f" ({i+1}) {fname.replace(NB_DIR + '/', '')} " + "="*3)
        num_converted += int(convert_notebook(fname))
    print("="*30)
    print("="*30 + f"\nConverted {num_converted}/{len(nb_fnames)} notebooks.\n" + "="*30)
