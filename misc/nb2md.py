import nbformat
import re
import os
# import logging
# logging.basicConfig(level=logging.DEBUG)
from nbconvert import MarkdownExporter
from nbconvert.writers import FilesWriter
from nbconvert.preprocessors import TagRemovePreprocessor
from jupyter_contrib_nbextensions.nbconvert_support.pre_pymarkdown import PyMarkdownPreprocessor
from traitlets.config import Config
from typing import NamedTuple
# may need to preprocess and run nb? 
#     https://stackoverflow.com/questions/39732784/minimal-example-of-how-to-export-a-jupyter-notebook-to-pdf-using-nbconvert-and-p
#     https://www.mprat.org/blog/2017/03/18/blogging-with-jupyter.html

class TagConfig(NamedTuple):
    tag: str
    block_start_tag: str
    block_end_tag: str

CURRENT_FILE = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
SITE_ROOT = os.path.abspath(os.path.join(CURRENT_FILE, ".."))
POSTS_PATH = os.path.abspath(os.path.join(SITE_ROOT, "_posts/notebook_posts"))
DRAFTS_PATH = os.path.abspath(os.path.join(SITE_ROOT, "_drafts/notebook_posts"))
HIDE_INPUT_TAG = TagConfig(
    tag="HIDE_INPUT",
    block_start_tag="HIDE_INPUT_START",
    block_end_tag="HIDE_INPUT_END")
HIDE_OUTPUT_TAG = TagConfig(
    tag="HIDE_OUTPUT",
    block_start_tag="HIDE_OUTPUT_START",
    block_end_tag="HIDE_OUTPUT_END")
HIDE_CELL_TAG = TagConfig(
    tag="HIDE_CELL",
    block_start_tag="HIDE_CELL_START",
    block_end_tag="HIDE_CELL_END")
DATE_PATTERN = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"

class CommentTagRemovePreprocessor(TagRemovePreprocessor):
    """
    Preprocessor for removing entire cells or just their inputs/outputs.
    Does so by recognizing specific code comments and turning them into tags,
    which are then processed by TagRemovePreprocessor.
    """
    def __init__(self, hide_input_config, hide_output_config, hide_cell_config, *args, **kwargs):
        self.enabled = True
        self.hide_input_config = hide_input_config
        self.hide_output_config = hide_output_config
        self.hide_cell_config = hide_cell_config
        super().__init__(*args, **kwargs)
        self.remove_input_tags = [hide_input_config.tag]
        self.remove_all_outputs_tags = [hide_output_config.tag]
        self.remove_cell_tags = [hide_cell_config.tag]

    def _apply_tag(self, cell, tag_config):
        """
        Applies a tag to the specified cell. Removes any tags from the
        comments of this cell.
        """
        if "metadata" not in cell or "tags" not in cell["metadata"]:
            cell["metadata"]["tags"] = cell.get("metadata", {}).get("tags", [])
        cell["metadata"]["tags"].append(tag_config.tag)

        # Remove comment indicating this tag from notebook cell
        inp = cell.get("source", "").split("\n")[0]
        if inp[0] == "#" and inp[1:].strip() in [tag_config.tag, tag_config.block_start_tag, tag_config.block_end_tag]:
            cell["source"] = "\n".join(cell.get("source", "").split("\n")[1:])

    def preprocess(self, nb, resources):
        cells = nb.cells
        tag_config_switches = {
            self.hide_input_config: False,
            self.hide_output_config: False,
            self.hide_cell_config: False
        }
        for cell in cells:
            inp = cell.get("source", "").split("\n")[0]
            # Exclude hashtag
            if len(inp) and inp[0] == "#":
                inp = inp[1:].strip()

            for config in tag_config_switches:
                if config.block_start_tag == inp:
                    tag_config_switches[config] = True
                    self._apply_tag(cell, config)
                elif config.block_end_tag == inp:
                    tag_config_switches[config] = False
                    self._apply_tag(cell, config)
                elif config.tag == inp or tag_config_switches[config]:
                    self._apply_tag(cell, config)


        nb.cells = cells
        return super().preprocess(nb, resources)


class NBExporter():
    def __init__(
        self,
        drafts_assets_dir="assets/notebook_files/drafts",
        posts_assets_dir="assets/notebook_files/posts",
        drafts_path=DRAFTS_PATH,
        posts_path=POSTS_PATH):
        
        self.drafts_assets_dir = drafts_assets_dir
        self.posts_assets_dir = posts_assets_dir
        self.drafts_path = drafts_path
        self.posts_path = posts_path

    @staticmethod
    def nb_name(fname):
        return "".join(os.path.basename(fname).split('.')[:-1])

    @staticmethod
    def get_assets_path(notebook_name, assets_root):
        return os.path.abspath(os.path.join(SITE_ROOT, assets_root, notebook_name))

    @staticmethod
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
        # txt = txt.replace(
        #     os.path.join(assets_root, NBExporter.nb_name(fname)),
        #     os.path.join(assets_root, NBExporter.nb_name(fname)) + "/")

        # Rewrite
        with open(fname, "w") as f:
            f.write(txt)

    @staticmethod
    def read_notebook(src):
        with open(src, "r") as f:
            return nbformat.read(f, as_version=4)

    def convert_to_markdown(self, src, notebook_name=None, date=None, draft=False):
        """Converts a Jupyter notebook to markdown and saves it in a posts or
        drafts directory. Makes appropriate modifications for Jekyll.

        Can run on a file path or an alraedy loaded nb object. If using a nb object,
        a notebook_name must be specified for use in the output file and directory names.

        Specify date to change the prepended date in the _posts folder.

        Args:
            src: File path to nb or a nb object.
            notebook_name: File/directory name to use when saving notebook and images.
                Will infer from src filename by default if src is a filename.
            date: Optional date to prepend when outputting to _posts folder. Will not be prepended anywhere else.
                  If a date already exists in the notebook name, an error will be thrown.
            draft: Whether to export as a draft to the draft directories. Defaults to False.
        """
        if type(src) == str:
            if notebook_name is None:
                notebook_name = NBExporter.nb_name(src)
            nb = NBExporter.read_notebook(src)
        # Assume it's a notebook, I should compare against actual nb type though
        else:
            if notebook_name is None or date is None:
                raise ValueError("Must specify notebook_name and date if using non file path src.")
            nb = src
        
        # Remove empty last cell if it exists
        if not nb.cells[-1].get("source", "").strip():
            nb.cells = nb.cells[:-1]

        # Handle date
        if date:
            if not re.match(DATE_PATTERN, date):
                raise ValueError("Date must match YYYY-MM-DD")
            if re.match(DATE_PATTERN, notebook_name):
                raise ValueError(f"Notebook name {notebook_name} already contains a date!")
            notebook_name_w_date = f"{date}-{notebook_name}"
        else:
            if not re.match(DATE_PATTERN, notebook_name):
                raise ValueError(
                    f"Notebook name {notebook_name} must contain a date if 'date' is unspecified!")
            notebook_name_w_date = notebook_name

        # Drafts go in _drafts folder
        if draft:
            dest = self.drafts_path
            assets_root = self.drafts_assets_dir
        else:
            dest = self.posts_path
            assets_root = self.posts_assets_dir

        c = Config()
        tag_preprocessor = CommentTagRemovePreprocessor(
            hide_cell_config=HIDE_CELL_TAG,
            hide_input_config=HIDE_INPUT_TAG,
            hide_output_config=HIDE_OUTPUT_TAG)
        c.MarkdownExporter.preprocessors = [
            tag_preprocessor,
            PyMarkdownPreprocessor(config=c),
        ]

        exporter = MarkdownExporter(config=c)
        writer = FilesWriter()
        writer.build_directory = dest

        # ExtractOutputPreprocessor will use this internally. It runs by default for all
        # Exporters. See Exporter base class for list of default preprocessors (only some of which are enabled)
        resources = {"output_files_dir": NBExporter.get_assets_path(notebook_name, assets_root=assets_root)}


        (body, resources) = exporter.from_notebook_node(nb, resources=resources)
        writer.write(body, resources, notebook_name=notebook_name_w_date)
        NBExporter.touchup_markdown(os.path.join(dest, notebook_name_w_date) + ".md")

# exp = NBExporter()
# exp.convert_to_markdown(
#     src="/home/alexm/projects/alexandermoore.github.io/src/python/2023-02-16-ROC-Vs-PR-AUC.ipynb",
#     draft=True)
