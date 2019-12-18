---
layout: post
title:  "How to Use Custom Objective Functions in XGBoost"
date:   2019-12-16 07:42:29 -0400
categories: jekyll update
---
I recently did some work on using custom objective functions in XGBoost. I ran into several hiccups along the way, so I've decided to share my findings here so that A) I don't forget them and B) others can perhaps get some benefit!

## The Basics

### What is an Objective Function?
An objective function (also called loss function) is a machine learning model's measure of success during training. It quantifies how well the model is fitting the data at any given time, where a larger number indicates a worse fit. The goal of the training process is typically to make the loss as small as possible. Since the model uses the loss function to measure success, we can change what it means for the model to be successful by changing the loss function!

For regression and classification, the loss is typically defined for each individual example and then aggregated across all examples to get a total loss. For example, suppose for a particular example $x_i$ our model predicts a score $\hat{y_i}$, but the correct answer was $y_i$. We might define the loss to be the square of the difference:

$$L(\hat{y_i}, y_i) = (\hat{y_i} - y_i)^2$$

If we had N total examples, the total loss would then be:

$$L(\hat{y}, y) = (\hat{y_1} - y_1)^2 + ... + (\hat{y_N} - y_N)^2 = \sum_{i=1}^{N} (\hat{y_i} - y_i)^2$$

Optionally the average can be taken by dividing the total by $N$.

You can learn more about how XGBoost works with objective functions [here][xgboost-boosting-intro].

### Objective Functions in XGBoost
In XGBoost, we are given an array of all the predictions $\hat{y_i}$ and an array of their labels $y_i$. To optimize the objective (a.k.a. loss) function, XGBoost needs to know the first derivative (gradient) of the loss for each example and the second derivative (hessian) of the loss for each example. These two values tell XGBoost how to adjust the scores to decrease the loss. The gradient tells us how much the loss would change by if we increased the score for a particular example. For instance, if the gradient is negative for a particular example, it means that increasing the score for that example would decrease the loss. So XGBoost will try and increase the score for examples like that one. The objective function signature is like this:

{% highlight python %}
def my_custom_objective(preds, dtrain):

    labels = dtrain.get_label()
    weight = dtrain.get_weight()

    gradient = ...
    hessian = ...
    
    return gradient, hessian
{% endhighlight %}

where:
* `preds` is an N-dimensional numpy array of all the predictions
* `dtrain` is a a special XGBoost object called a `DMatrix`. The `DMatrix` contains information about the dataset, and it allows us to retrieve the `labels` and `weights` for our training data. More on this later.
* `gradient` is an N-dimensional numpy array of the gradient of the loss function with respect to each prediction score.
* `hessian` is an N-dimensional numpy array of the hessian of the loss function with respect to each prediction score.

There are common objective functions used in machine learning for classification and regression. XGBoost already implements these internally and provides ways to utilize them. But if you want to implement your own, you'll need to define a custom objective like we did above.


### Seeing a Custom Objective in Action

It's important to note that our objective function can be whatever we want. It would be silly, but we don't have to use `labels` or `weights` at all if we don't want to. For example, say we just wanted XGBoost to predict as large a number as possible for each example. We might define our loss function like this:

$$
L(\hat{y_i}, y_i) = -\hat{y_i}
$$

For this to be as small as possible, $\hat{y_i}$ should be as large as possible. Let's see if it works. Here are the derivatives:
* gradient = $\frac{\partial L}{\hat{y_i}} = -1 $
* hessian = $\frac{\partial^2 L}{\hat{y_i}^2} = 0 $

Implemented in terms of `preds` our objective function would be:
```
objective = -preds
```

Since XGBoost only wants the gradient and hessian of the loss function, we can just provide those:

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

On the other hand, if we use a more reasonable loss function like the squared error we described earlier (we can divide it by 2 so the derivative looks a little nicer), we should see XGBoost predict the labels well.

$$
L(\hat{y_i}, y_i) = \frac{1}{2}(\hat{y_i} - y_i)^2
$$

Here are the derivatives:
* gradient = $\frac{\partial L}{\hat{y_i}} = (\hat{y_i} - y_i) $
* hessian = $\frac{\partial^2 L}{\hat{y_i}^2} = 1 $

Running our same code:

{% highlight python %}
X = np.array([[1,2,0],
              [1,1,2],
              [5,2,1]])

y = np.array([5,-3,2])

dtrain = xgb.DMatrix(data=X, label=y)

def squared_loss(preds, dtrain):
    N = preds.shape[0]
    labels = dtrain.get_label()
    
    gradient = (preds - labels)
    hessian =  np.ones(N)
    
    return gradient, hessian

model = xgb.train(params={},
                  dtrain=dtrain,
                  obj=squared_loss,
                  num_boost_round=100)

model.predict(dtrain)
{% endhighlight %}
Output:
```
array([ 4.9989624 , -2.99893665,  1.99997354], dtype=float32)
```
As expected, XGBoost is making predictions very close to our labels `y`.

You can see another example of using a custom objective function [in the XGBoost Tutorial here][xgboost-reg-tutorial].

## Practical Concerns
### Practical Concerns for Classification
All the examples above were for regression as opposed to classification, but internally XGBoost doesn't know the difference. If we're using a classification objective function, we'll get a classifier.

For example, using the cross-entropy loss function:

$$
L(y, p) = -y log(p) - (1 - y) log(1 - p)
$$

where in this case, $\hat{y}$ is first transformed from a raw number to a number $p$ between 0 and 1 via the sigmoid function:

$$
p = \frac{1}{1 + e^{-\hat{y}}}
$$

you can train a classifier. XGBoost provides an example of this loss function [here][xgboost-class-code]. I'll paste it below:

{% highlight python %}
def logregobj(preds, dtrain):
    labels = dtrain.get_label()
    preds = 1.0 / (1.0 + np.exp(-preds))
    grad = preds - labels
    hess = preds * (1.0 - preds)
    return grad, hess
{% endhighlight %} 

*IMPORTANT*: XGBoost is still predicting $\hat{y}$, not $p$, so you'll have to apply the sigmoid function to any predictions made to get $p$:

{% highlight python %}
model = xgb.train(params={},
                  dtrain=dtrain,
                  obj=logregobj,
                  num_boost_round=100)

raw_predictions = model.predict(dataset)
probabilities = 1.0 / (1 + np.exp(-raw_predictions))
{% endhighlight %} 

It is possible to make XGBoost automatically apply the sigmoid transformation to all predictions, even before entering the loss function. To do this, pass the following `objective` parameter to the `xgb.train()` method:

{% highlight python %}
model = xgb.train(params={"objective": "binary:logistic"},
                  dtrain=dtrain,
                  obj=logregobj,
                  num_boost_round=100)
{% endhighlight %}

While ordinarily this would cause XGBoost to treat the problem as a classification problem, optimize the cross entropy loss, and predict probabilities, when we provide a custom objective function the default cross entropy objective is overriden. So all `"objective": "binary:logistic"` does is transform the model scores using the sigmoid function. The scores are transformed before entering the loss function as well as when the `.predict` method is called. Since the transformation is happening automatically, our above code simply becomes:

{% highlight python %}
def logregobj(preds, dtrain):
    labels = dtrain.get_label()
    # We don't need to do this anymore-- preds is already transformed
    # preds = 1.0 / (1.0 + np.exp(-preds))
    grad = preds - labels
    hess = preds * (1.0 - preds)
    return grad, hess

model = xgb.train(params={"objective": "binary:logistic"},
                  dtrain=dtrain,
                  obj=logregobj,
                  num_boost_round=100)

raw_predictions = model.predict(dataset)
# we don't need to do this anymore-- raw_predictions is already transformed
# probabilities = 1.0 / (1 + np.exp(-raw_predictions))
probabilities = raw_predictions
{% endhighlight %} 

Here's a full example:

**Without using the `objective` parameter:**
{% highlight python %}
# Create some dummy classification data
np.random.seed(123)
N = 1000
X = np.random.normal(loc=0, scale=4.0, size=(N, 10))
split_point = 600
X_train = X[:split_point]
X_test = X[split_point:]

# Create some labels based on the data
y_train = X_train[:, 3] + X_train[:, 6] + np.random.normal(loc=0, scale=0.2, size=(X_train.shape[0],))
y_test = X_test[:, 3] + X_test[:, 6] + np.random.normal(loc=0, scale=0.2, size=(X_test.shape[0],))

y_train = (y_train > 0).astype(np.int32)
y_test = (y_test > 0).astype(np.int32)

print("y_train[:10]", y_train[:10])
print("y_test[:10]", y_test[:10])

def logregobj(preds, dtrain):
    labels = dtrain.get_label()
    preds = 1.0 / (1.0 + np.exp(-preds))
    grad = preds - labels
    hess = preds * (1.0 - preds)
    return grad, hess


dtrain = xgb.DMatrix(data=X_train, label=y_train)
dtest = xgb.DMatrix(data=X_test, label=y_test)

model = xgb.train(params={},
                  dtrain=dtrain,
                  obj=logregobj,
                  num_boost_round=100)

raw_predictions = model.predict(dtest)
probabilities = 1.0 / (1.0 + np.exp(-raw_predictions))

print("\nRaw Predictions:")
print(raw_predictions[:10])
print("\nProbabilities:")
print(probabilities[:10])
print("\nTotal Accuracy:", ((probabilities >= 0.50) == y_test).sum()/y_test.shape[0])
{% endhighlight %}

Output:
```
y_train[:10] [0 1 1 0 1 1 0 0 1 1]
y_test[:10] [1 1 0 1 0 0 0 1 0 0]

Raw Predictions:
[ 7.27056217  8.49974632  1.99836755  1.20859027 -7.84369659 -6.40357876
 -6.0802598   2.70093369 -2.56601596 -5.41519356]

Probabilities:
[ 0.99930477  0.99979657  0.88062561  0.77004939  0.00039206  0.00165289
  0.00228236  0.93708169  0.07135786  0.00442878]

Total Accuracy: 0.9575
```

**With the `objective` hyperparameter:**
{% highlight python %}
# Create some dummy classification data
np.random.seed(123)
N = 1000
X = np.random.normal(loc=0, scale=4.0, size=(N, 10))
split_point = 600
X_train = X[:split_point]
X_test = X[split_point:]

# Create some labels based on the data
y_train = X_train[:, 3] + X_train[:, 6] + np.random.normal(loc=0, scale=0.2, size=(X_train.shape[0],))
y_test = X_test[:, 3] + X_test[:, 6] + np.random.normal(loc=0, scale=0.2, size=(X_test.shape[0],))

y_train = (y_train > 0).astype(np.int32)
y_test = (y_test > 0).astype(np.int32)

print("y_train[:10]", y_train[:10])
print("y_test[:10]", y_test[:10])

def logregobj(preds, dtrain):
    labels = dtrain.get_label()
    # preds = 1.0 / (1.0 + np.exp(-preds))
    grad = preds - labels
    hess = preds * (1.0 - preds)
    return grad, hess


dtrain = xgb.DMatrix(data=X_train, label=y_train)
dtest = xgb.DMatrix(data=X_test, label=y_test)

model = xgb.train(params={"objective": "binary:logistic"},
                  dtrain=dtrain,
                  obj=logregobj,
                  num_boost_round=100)

raw_predictions = model.predict(dtest)
probabilities = raw_predictions

print("\nRaw Predictions:")
print(raw_predictions[:10])
print("\nProbabilities:")
print(probabilities[:10])
print("\nTotal Accuracy:", ((probabilities >= 0.50) == y_test).sum()/y_test.shape[0])
{% endhighlight %}

Output:
```
y_train[:10] [0 1 1 0 1 1 0 0 1 1]
y_test[:10] [1 1 0 1 0 0 0 1 0 0]

Raw Predictions:
[ 0.99937856  0.99973887  0.79718798  0.96075255  0.00050697  0.00167991
  0.00208455  0.88085169  0.07331276  0.00292544]

Probabilities:
[ 0.99937856  0.99973887  0.79718798  0.96075255  0.00050697  0.00167991
  0.00208455  0.88085169  0.07331276  0.00292544]

Total Accuracy: 0.9575
```

[jekyll-docs]: https://jekyllrb.com/docs/home
[jekyll-gh]:   https://github.com/jekyll/jekyll
[jekyll-talk]: https://talk.jekyllrb.com/
[xgboost-boosting-intro]: https://xgboost.readthedocs.io/en/latest/tutorials/model.html
[xgboost-reg-tutorial]: https://xgboost.readthedocs.io/en/latest/tutorials/custom_metric_obj.html
[xgboost-class-code]: https://github.com/dmlc/xgboost/blob/master/demo/guide-python/custom_objective.py
