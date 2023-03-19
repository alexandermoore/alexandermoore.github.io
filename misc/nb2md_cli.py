import argparse
import os
import re
import logging
logging.basicConfig(level=logging.WARNING)
from dataclasses import dataclass
from nb2md import NBExporter, DATE_PATTERN, SITE_ROOT
from datetime import datetime
from watchdog.observers import Observer
import watchdog.events
import time
import pathlib

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

# class PollingUpdateHandler(watchdog.events.PatternMatchingEventHandler):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._last_converted = {}
#         self._blocked = {}

#     def _process(self, event):
#         curr_time = time.time()
#         # Temporary ".~" until figure out ignore_pattern issue.
#         if ".~" in event.src_path:
#             return
#         # Modified event triggers twice for some reason so only update once per 2 seconds.
#         #   maybe this: https://github.com/gorakhargosh/watchdog/issues/93
#         if curr_time - self._last_converted.get(event.src_path, 0) <= 1:
#             return
#         self._last_converted[event.src_path] = curr_time
#         print("WANT TO CONVERT", os.path.abspath(event.src_path))
#         while self._blocked.get(event.src_path):
#             pass
#         self._blocked[event.src_path] = True
#         convert_notebook(os.path.abspath(event.src_path))
#         self._blocked[event.src_path] = False

#     def on_created(self, event):
#         self._process(event)
#     def on_modified(self, event):
#         self._process(event)
        

# def run_polling_updates(fname=None):

#     patterns = ["*.ipynb" if not fname else os.path.relpath(fname, NB_DIR)]
#     event_handler = PollingUpdateHandler(
#         patterns=patterns,
#         # .~ are some jupyter temp files
#         ignore_patterns=[".ipynb_checkpoints", "\.\~"],
#         ignore_directories=True)
#     observer = Observer()
#     observer.schedule(event_handler, NB_DIR, recursive=False)
#     observer.start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()

def run_polling_updates(fname=None):
    # I tried using watchdog but notebook file reads started coming up empty.. maybe a concurrency
    # issue or something. This suits my needs fine.
    fnames = [fname] if fname else list_notebooks(NB_DIR)
    last_modified = {fname: pathlib.Path(fname).stat().st_mtime for fname in fnames}
    while True:
        for fname in fnames:
            if last_modified[fname] != pathlib.Path(fname).stat().st_mtime:
                print(f"({datetime.now().strftime(r'%m/%d %I:%M:%S %p')}) Change detected: {fname}")
                last_modified[fname] = pathlib.Path(fname).stat().st_mtime
                print("Conversion success?", convert_notebook(fname))
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert notebook(s) to markdown')
    parser.add_argument(
        '--fname',
        type=str,
        default=None)
    parser.add_argument(
        '--dest',
        type=str, 
        default=None)
    parser.add_argument(
        "--poll",
        action="store_true",
        default=False,
        help="Whether to run continuously and poll files/folder for changes")
    parser.add_argument(
        "--no_initial_convert",
        action="store_true",
        default=False,
        help="Whether to run convert initially")
    # parser.add_argument("--img_path", type=str, default=None)
    # parser.add_argument("--jekyll", action="store_true", default=None)
    # parser.add_argument("--all", action="store_true", default=None)
    #args_dict = vars(parser.parse_args())
    args = parser.parse_args()

    if args.no_initial_convert and not args.poll:
         logging.warn("Nothing will happen since no initial convert or polling is happening.")

    if not args.no_initial_convert:
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
    
    if args.poll:
        print("Polling for changes...")
        run_polling_updates(args.fname)
