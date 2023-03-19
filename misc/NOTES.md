---
search_exclude: True
---

# Notes
To fix webrick issue:
```
bundle add webrick
```

$f(x) = 7^2$

```
cat $(bundle show minima)
```

Cairo pango
```
sudo apt-get install libpango1.0-dev
sudo apt-get install libcairo2-dev
sudo apt install texlive-full
```

# nbextensions
```
pip install jupyter_contrib_nbextensions
jupyter contrib nbextension install --user
jupyter nbextensions_configurator enable --user
```
Also must set notebook to trusted `File -> Trust this notebook`

### How this is organized

Folders:
* `_posts` contains posts. `notebook_posts` subfolder contains results outputted by `nb2md_cli.py`.
* `_drafts` has the same format as `_posts` but is for drafts.
* `assets` contains assets. `notebook_files/posts` and `notebook_files/drafts` contain assets for posts and drafts (each nb gets its own folder) outputted via `nb2md_cli.py`.

Notebook frontmatter custom options (see `nb2md_cli.py`):
* `_date`: Specify a date in `YYYY-MM-DD` format or write `today` to use today's date.
* `_publish_`: Whether to publish this notebook, as a draft or post. If not specified, notebook is NOT published! Set to `true` or `false`.
* `_draft`: Whether to publish this post as a draft or not (by default, it will be published as a post. Set to `true` or `false`)

Run `nb2md_cli.py` to convert notebooks once, use the shortcut `run_nb2md_polling.sh` to monitor for changes and convert changed notebooks.

Run `misc/build_prod_site.sh` to build the non-draft version of the site in the `_site` folder.

Run `misc/deploy_prod_site.sh` to kill and nb2md_cli and jekyll instances, build prod website from scratch, and push it to master.