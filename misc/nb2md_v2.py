import nbformat
import re
import os
from nbconvert import HTMLExporter, MarkdownExporter
from nbconvert.writers import FilesWriter
from nbconvert.preprocessors import ExtractOutputPreprocessor, TagRemovePreprocessor
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
MARKDOWN_PATH = os.path.abspath(os.path.join(SITE_ROOT, "_posts/notebook_posts"))
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
DATE_PATTERN = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-"
NB_ASSETS_DIR = "assets/notebook_files"

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

class ExtractOutputPreprocessorWithDir(ExtractOutputPreprocessor):
    """
    TODO: Find a nicer way to do this. There must be a way to set the output directory
          in ExtractOutputPreprocessor.
    """
    def __init__(self, output_dir, *args, **kwargs):
        self._custom_output_dir = output_dir
        return super().__init__(*args, **kwargs)
    
    def preprocess_cell(self, cell, resources, cell_index):
        if resources is None:
            resources = {}
        resources["output_files_dir"] = self._custom_output_dir
        return super().preprocess_cell(cell, resources, cell_index)

class NBExporter():
    @staticmethod
    def nb_name(fname):
        return "".join(os.path.basename(fname).split('.')[:-1])

    @staticmethod
    def imgpath(notebook_name):
        return os.path.abspath(os.path.join(SITE_ROOT, NB_ASSETS_DIR, notebook_name))

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
        txt = txt.replace(
            os.path.join(NB_ASSETS_DIR, NBExporter.nb_name(fname)),
            os.path.join(NB_ASSETS_DIR, NBExporter.nb_name(fname)) + "/")

        # Rewrite
        with open(fname, "w") as f:
            f.write(txt)

    def to_markdown(self, src, dest=None, draft=False, draft_replace_date="NBDRAFT"):
        notebook_name = NBExporter.nb_name(src)
        if dest is None:
            # Drafts go in _drafts folder and have no date
            if draft:
                dest = DRAFTS_PATH 
                notebook_name = re.sub(DATE_PATTERN, f'{draft_replace_date}-', notebook_name)
            else:
                dest = MARKDOWN_PATH
        c = Config()
        tag_preprocessor = CommentTagRemovePreprocessor(
            hide_cell_config=HIDE_CELL_TAG,
            hide_input_config=HIDE_INPUT_TAG,
            hide_output_config=HIDE_OUTPUT_TAG)
        c.MarkdownExporter.preprocessors = [
            tag_preprocessor,
            PyMarkdownPreprocessor(config=c),
            ExtractOutputPreprocessorWithDir(output_dir=NBExporter.imgpath(notebook_name))
        ]
        exporter = MarkdownExporter(config=c)
        writer = FilesWriter()
        writer.build_directory = dest
        with open(src, "r") as f:
            nb = nbformat.read(f, as_version=4)
        (body, resources) = exporter.from_notebook_node(nb)
        writer.write(body, resources, notebook_name=notebook_name)
        NBExporter.touchup_markdown(os.path.join(dest, notebook_name) + ".md")

exp = NBExporter()
exp.to_markdown(
    "/home/alexm/projects/alexandermoore.github.io/src/python/2023-02-16-ROC-Vs-PR-AUC.ipynb",
    draft=True)
