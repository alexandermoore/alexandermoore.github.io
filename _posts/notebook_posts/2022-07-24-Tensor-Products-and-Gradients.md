---
layout: post
permalink: tensor-products-grads
title: A Way to Understand Shapes of Matrix Products and Gradients
---

    
![png](/assets/nb_files/2022-07-24-Tensor-Products-and-Gradients/output_1_0.png)
    


Gradients are everywhere in deep learning, but I sometimes get tripped up by their shapes. Taking the derivative of a scalar with respect to a scalar is one thing, but what about a vector and a vector, or a matrix and a matrix? What are the dimensions then?

In this post I hope to clarify some of these by building up from this basic concept:
> The derivative $\frac{dy}{dx}$ tells you how much $y$ changes when you change $x$ by a little bit.

$x$ and $y$ could be anything here-- scalars, vectors, matrices or tensors.

From this concept, we can already learn something about the shape of $\frac{dy}{dx}$. It must somehow tell us, for each dimension of $x$, how much a small difference in that dimension would change $y$. We'll make this clearer as we go.

### Scalar and a scalar
First let's see a concrete example of how this works with scalars. Consider the following simple function:\$\$ y = x^2 \$\$
We know the derivative of this is:

{% raw %}
\$\$ \frac{dy}{dx} = 2x \$\$
{% endraw %}

If we change $x$ by a little bit, $y$ will change by $2x$. Applying our concept above, $\frac{dy}{dx}$ looks at each dimension of $x$ and tells us how much a small difference in it would change each dimension of $y$. Since $y$ only has one dimension and $x$ only has one dimension, there's only one change to look at. So $\frac{dy}{dx}$ also has one dimension.

### Vector and a scalar
Now let's consider a scalar $x$ and a vector $\mathbf{y}$ like so:


\$\$
\mathbf{y} = (x^2, x^3, x^4)
\$\$

In this case, we want to know how much a change in $x$ will impact each dimension of $y$.

\$\$
\frac{d\mathbf{y}}{dx} = (\frac{d(x^2)}{dx}, \frac{d(x^3)}{dx}, \frac{d(x^4)}{dx})
\$\$

This post. And another line.

```python
import re
```

```python
pattern="---\n.*\n---"
s = """
# Tensor Products and Gradients


---
layout: post
permalink: other-url
---
# Title



This post. And another line.

"""
re.search(pattern, s, re.DOTALL).group()
```




    '---\nlayout: post\npermalink: other-url\n---'



```python
d = "2022-05-something"
re.search("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-", d)
```
