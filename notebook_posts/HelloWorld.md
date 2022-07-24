# Some cell



```python
import numpy
```

Hello world $f(x) = 5$ is a function.

```python
print("hey")
```

    hey


```python
from nbdev.export2html import nbdev_nb2md
```

```python
#nbdev_nb2md("HelloWorld.ipynb")
import nbdev
nbdev.__version__
```




    '1.2.11'



```python
help(nbdev_nb2md)
```

    Help on function nbdev_nb2md in module nbdev.export2html:
    
    nbdev_nb2md(fname: str, dest: str = '.', img_path: None = '', jekyll: <function bool_arg at 0x7f8dc1de4700> = False)
        Convert the notebook in `fname` to a markdown file
    

