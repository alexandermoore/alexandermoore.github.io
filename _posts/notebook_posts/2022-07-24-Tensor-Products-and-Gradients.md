---
layout: post
permalink: tensor-products-grads
title: Understanding Shapes of Matrix Products and Gradients
---
Taking the derivative of a scalar with respect to a scalar is one thing, but what about a vector and a vector, or a matrix and a matrix? What are the dimensions then?

In this post I hope to clarify some of these by applying this key concept over and over:
> The derivative $\frac{dy}{dx}$ tells you how much $y$ changes when you increase $x$ by a little bit.

$x$ and $y$ could be anything here-- scalars, vectors, matrices or tensors.

From this concept, we can already learn something about the shape of $\frac{dy}{dx}$. It must somehow tell us, for each dimension of $y$, how much a small increase in each dimension of $x$ would change it by.

## Scalar and a scalar
First let's see a concrete example of how this works with scalars (numbers). Consider the following function:\$\$ y = x^2 \$\$
We know the derivative of this is:

{% raw %}
\$\$ \frac{dy}{dx} = 2x \$\$
{% endraw %}

If we increase $x$ by a little bit, $y$ will increase by $2x$. Applying our concept above, $\frac{dy}{dx}$ looks at each dimension of $y$ and tells us how much a small increase in $x$ would change it by. Since $y$ only has one dimension and $x$ only has one dimension, there's only one change to look at. So $\frac{dy}{dx}$ also has one dimension.

## Vector and a scalar
Now let's consider a a vector $\mathbf{y}$ and scalar $x$ like so:


\$\$ \mathbf{y} = \begin{bmatrix} a \\\ b \\\ c \end{bmatrix} \$\$

From now on I'll write values like $a$, $b$, $c$ instead of using actual functions of $x$, which should keep things a little cleaner. Just imagine each of $a$, $b$, $c$ somehow depends on $x$. For example, maybe $a = x^2$.

Applying our concept again, $\frac{d\mathbf{y}}{dx}$ looks at each dimension of $\mathbf{y}$ to see how much a small increase in $x$ would change it by. Since there are 3 dimensions in $\mathbf{y}$ to look at and only one in $x$, we would expect $\frac{d\mathbf{y}}{dx}$ to have 3 dimensions. Each dimension should tell us how much a small increase in $x$ will change that dimension of $\mathbf{y}$ by.

If we carry out this logic and do the math:
\$\$ \frac{d\mathbf{y}}{dx} = \begin{bmatrix} \frac{da}{dx} \\\ \frac{db}{dx} \\\ \frac{dc}{dx} \end{bmatrix} \$\$

We see that $\frac{d\mathbf{y}}{dx}$ indeed has 3 dimensions as expected. The first one tells us how much the first dimension of $\mathbf{y}$ changes by when we increase $x$ by a small amount. The second tells us how much the second dimension of $\mathbf{y}$ changes by when we increase $x$ by a small amount. And same for the third.

## Scalar and a vector:
Now let's flip the above! Let's make $y$ a scalar and $\mathbf{x}$ a vector:

\$\$ \mathbf{x} = \begin{bmatrix} a \\\ b \\\ c \end{bmatrix} \$\$

We want to know:

\$\$ \frac{dy}{d\mathbf{x}} \$\$

We can apply the same concept again. $\frac{dy}{d\mathbf{x}}$ looks at each dimension of $y$ and tells us how much a small increase in $\mathbf{x}$ will change it by. But this time $\mathbf{x}$ has 3 dimensions and $y$ has only one dimension. So, $\frac{dy}{d\mathbf{x}}$ will tell us how much the one dimension of $y$ is changed by _each_ of the 3 dimensions of $\mathbf{x}$. It will have 3 dimensions like so:

\$\$ \frac{dy}{d\mathbf{x}}= \begin{bmatrix} \frac{dy}{da} & \frac{dy}{db} & \frac{dy}{dc} \end{bmatrix} \$\$

As an aside, you may be wondering why I wrote the derivative vector horizontally, and how to know when it should be horizontal or vertical? I could have just as easily written this:

\$\$ \frac{dy}{d\mathbf{x}}= \begin{bmatrix} \frac{dy}{da} \\\ \frac{dy}{db} \\\ \frac{dy}{dc} \end{bmatrix} \$\$

There are actually two [conventions](https://en.wikipedia.org/wiki/Matrix_calculus#Layout_conventions) about which way to do it, but not everyone is consistent. I've picked the one where the derivative's "numerator" is the same in every row, and I'll will stick to that for the rest of this post!


## Vector and a vector
Now things are getting interesting! We'll make $\mathbf{x}$ and $\mathbf{y}$ both vectors now:

\$\$ \mathbf{x} = \begin{bmatrix} a \\\ b \\\ c \end{bmatrix} \$\$

\$\$ \mathbf{y} = \begin{bmatrix} q \\\ r \end{bmatrix} \$\$

And we want to know:

\$\$ \frac{d\mathbf{y}}{d\mathbf{x}} \$\$

We can again apply the same concept! We want to know how much each dimension of $\mathbf{y}$ is changed by each dimension of $\mathbf{x}$. 

$\mathbf{y}$ has 2 dimensions, and for each of those 2 dimensions we need to check how each of the 3 dimensions of $\mathbf{x}$ will change it by. So we expect $\frac{d\mathbf{y}}{d\mathbf{x}}$ to have 2x3 = 6 different entries.
They are usually arranged into a matrix like so (again I'll keep the derivative numerator the same in each row):

\$\$ \frac{d\mathbf{y}}{d\mathbf{x}} =  \begin{bmatrix}  \frac{dq}{da} & \frac{dq}{db} & \frac{dq}{dc} \\\ \frac{dr}{da} & \frac{dr}{db} & \frac{dr}{dc} & \end{bmatrix} \$\$

You may be noticing a pattern:
1. 


In this matrix, position $(i, j)$ tells you how much the $i^{th}$ dimension of $\mathbf{y}$ changes when you change the $j^{th}$ dimension of $\mathbf{x}$ by a little bit. For example, position $(2, 1)$, the one containing $\frac{dr}{da}$, tells us how much the 2nd dimension of $\mathbf{y}$ changes when we change the 1st dimension of $\mathbf{x}$ by a little bit.

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

```python
pattern=r"(\$\$.+?\$\$)"
s = r"""
Now let's begin
\$\$ some \\\ text \\\ \$\$
and then \\
\$\$ hello \\\ world \$\$
ok
"""
for t in re.findall(pattern, s, re.DOTALL):
    tt = t.replace("\\\\", "\\\\\\")
    s = s.replace(t, tt)
print(s)
```

    
    Now let's begin
    \$\$     some \\\\ text \\\\     \$\$
    and then \\
    \$\$     hello \\\\ world     \$\$
    ok
    

