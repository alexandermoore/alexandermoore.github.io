---
layout: post
title:  "How to Use Custom Objective Functions in XGBoost"
date:   2019-12-16 07:42:29 -0400
categories: jekyll update
---
I recently did some work on using custom objective functions in XGBoost. I ran into several hiccups along the way, so I've decided to share my findings here so that A) I don't forget them and B) others can perhaps get some benefit!


### What is an Objective Function?
An objective function (also called loss function) is a machine learning model's measure of success during training. It quantifies how well the model is fitting the data at any given time, where a larger number indicates a worse fit. The goal of the training process is typically to make the loss as small as possible. Since the model uses the loss function to measure success, we can change what it means for the model to be successful by changing the loss function!

For regression and classification, the loss is typically defined for each individual example and then aggregated across all examples to get a total loss. For example, suppose for a particular example $x_i$ our model predicts a score $\hat{y_i}$, but the correct answer was $y_i$. We might define the loss to be the square of the difference:

$$L(\hat{y_i}, y_i) = (\hat{y_i} - y_i)^2$$

If we had N total examples, the total loss would then be:

$$L(\hat{y}, y) = (\hat{y_1} - y_1)^2 + ... + (\hat{y_N} - y_N)^2 = \sum_{i=1}^{N} (\hat{y_i} - y_i)^2$$

Optionally the average can be taken by dividing the total by $N$.

### Objective Functions in XGBoost
In XGBoost, we are given an array of all the predictions $\hat{y_i}$ and an array of their labels $y_i$. To optimize the objective function, XGBoost needs to know the first derivative (gradient) of the loss for each example and the second derivative (hessian) of the loss for each example. These two values tell XGBoost how to adjust the scores to decrease the loss. The gradient tells us how much the loss would change by if we increased the score for a particular example. For instance, if the gradient is negative for a particular example, it means that increasing the score for that example would decrease the loss. So XGBoost will try and increase the score for examples like that one. The objective function signature is like this:

{% highlight python %}
def my_custom_objective(preds, dtrain):

    labels = dtrain.get_labels()

    gradient = ...
    hessian = ...
    
    return gradient, hessian
{% endhighlight %}

where:
* `preds` is an N-dimensional numpy array of all the predictions
* `dtrain` is a a special XGBoost object called a `DMatrix`. The `DMatrix` contains information about the dataset, and it allows us to retrieve the `labels` and `weights` for our training data. More on this later.
* `gradient` is an N-dimensional numpy array of the gradient of the loss function with respect to each prediction score.
* `hessian` is an N-dimensional numpy array of the hessian of the loss function with respect to each prediction score.

It's important to note that our objective function can be whatever we want. It would be silly, but we don't have to use `labels` or `weights` at all if we don't want to. For example, say we just wanted XGBoost to predict as large a number as possible for each example. We might define our loss function like this:

$$
L(\hat{y_i}, y_i) = -y_i
$$

The derivatives are:
* $\frac{\partial L}{\hat{y_i}} = -1 $
* $\frac{\partial^2 L}{\hat{y_i}^2} = 0 $

Implemented in terms of `preds` and `labels`, our objective function would be:
```
objective = -preds
```
but since XGBoost only wants the gradient and hessian of the loss function, we can just provide those:

{% highlight python %}
def large_numbers_objective(preds, dtrain):
    N = preds.shape[0]
    
    gradient = np.ones(N) * -1
    hessian = np.zeros(N)
    
    return gradient, hessian
{% endhighlight %}

Let's see if what we expect happens. XGBoost should ignore the labels and just make the score larger and larger the more iterations we do. Here's a toy example with 3 rows of data:

{% highlight python %}
X = np.array([[1,2,0],
              [1,1,2],
              [5,2,1]])

y = np.array([5,-5,2])

dtrain = xgb.DMatrix(data=X, label=y)

def large_numbers_objective(preds, dtrain):
    N = preds.shape[0]
    
    gradient = np.ones(N) * -1
    hessian = np.zeros(N)
    
    return gradient, hessian

model = xgb.train(params={}, 
                  dtrain=dtrain, 
                  obj=large_numbers_objective,
                  num_boost_round=10)

model.predict(dtrain)
{% endhighlight %}

This outputs:
```
array([ 9.5,  9.5,  9.5], dtype=float32)
```

As expected, the labels are being ignored completely. We should expect the scores to increase the higher `num_boost_round` is. Let's see:

{% highlight python %}
model = xgb.train(params={}, 
                  dtrain=dtrain, 
                  obj=large_numbers_objective,
                  num_boost_round=100)

model.predict(dtrain)
{% endhighlight %}

```
array([ 90.50008392,  90.50008392,  90.50008392], dtype=float32)
```

{% highlight python %}
model = xgb.train(params={}, 
                  dtrain=dtrain, 
                  obj=large_numbers_objective,
                  num_boost_round=1000)

model.predict(dtrain)
{% endhighlight %}

```
array([ 900.50805664,  900.50805664,  900.50805664], dtype=float32)
```

Indeed, XGBoost is optimizing our objective as desired by making the scores as large as possible. 


## Defining a Custom Objective
The [XGBoost Tutorial][xgb-reg-tutorial] covering "log squared error"
$$
x^{2} = 7
$$


Take the equation $y^3$

Jekyll requires blog post files to be named according to the following format:

`YEAR-MONTH-DAY-title.MARKUP`

Where `YEAR` is a four-digit number, `MONTH` and `DAY` are both two-digit numbers, and `MARKUP` is the file extension representing the format used in the file. After that, include the necessary front matter. Take a look at the source for this post to get an idea about how it works.

Jekyll also offers powerful support for code snippets:

{% highlight ruby %}
def print_hi(name)
  puts "Hi, #{name}"
end
print_hi('Tom')
#=> prints 'Hi, Tom' to STDOUT.
{% endhighlight %}

Check out the [Jekyll docs][jekyll-docs] for more info on how to get the most out of Jekyll. File all bugs/feature requests at [Jekyll’s GitHub repo][jekyll-gh]. If you have questions, you can ask them on [Jekyll Talk][jekyll-talk].

[jekyll-docs]: https://jekyllrb.com/docs/home
[jekyll-gh]:   https://github.com/jekyll/jekyll
[jekyll-talk]: https://talk.jekyllrb.com/
[xgboost-reg-tutorial]: https://xgboost.readthedocs.io/en/latest/tutorials/custom_metric_obj.html
[xgboost-class-code]: https://github.com/dmlc/xgboost/blob/master/demo/guide-python/custom_objective.py
