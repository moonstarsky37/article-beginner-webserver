[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/moonstarsky37/article-beginner-webserver/blob/gh-pages/LICENSE)

#Ziyu-blog
This page only list some article basic idea.

## Article : [Python網站部署的基本流程-for beginner](https://moonstarsky37.github.io/article-beginner-webserver/article1.html)

當你想要架構一個網站的時候，我們也必須先知道一些關於網站是如何呈現給人的知識
再者，我們瞭解了這些基本之後，我們又應該從哪些框架(framework)開始練習比較好。
最後我們又應該如何讓我們所做的這些專案給別人看到呢。

### Outline:

- What is a web server
- How to use a web server
- Deploy your web

------------------

## Article : Use Jupyter notebok to see the RNN(LSTM) result.

When I make a introduction to RNN, I use the MNIST data set.
I modify the keras
[example](https://github.com/fchollet/keras/blob/master/examples/mnist_hierarchical_rnn.py) to Jupyter ver.

Also, in order to comepare the code style between two Keras model.
I also make both of them in the same NN.

The [Model](http://nbviewer.jupyter.org/github/moonstarsky37/article-beginner-webserver/blob/gh-pages/mnist_model_architecture_Rnn_LSTM_Model.ipynb)
version.

The [Sequential](http://nbviewer.jupyter.org/github/moonstarsky37/article-beginner-webserver/blob/gh-pages/mnist_model_architecture_Rnn_LSTM_Sequential.ipynb)
version.

------------------


## Article : Use real data from UCI

After some introduction of NN, we want to use more real data to practice.
We use the datasets form the [UCI datasets](http://archive.ics.uci.edu/ml/datasets.html).

We use the [Diabetes datasets](http://archive.ics.uci.edu/ml/datasets/Pima+Indians+Diabetes) as example.
The .data is a csv file, and the column from one to eight is some features of patients and last column is whether the patient have diabetes.

The result is below.
[Diabetes practice](http://nbviewer.jupyter.org/github/moonstarsky37/article-beginner-webserver/blob/gh-pages/NN-practice-pima-indians-diabetes.ipynb)


------------------


## Article : Visualization of relationship of obo file

Sometimes when we need to see the go-term relation, we will present as a set.
We also want to see visualization part.I simplfy to just a simple code
from [here](https://github.com/tanghaibao/goatools) .
This code can get the figure like
![obo-relationship](https://github.com/moonstarsky37/article-beginner-webserver/blob/gh-pages/obo_relationships/relation.png)

Just need
```
python main.py --id=GOTERMID PATH
```
where the PATH need to use your [obo file](http://geneontology.org/page/download-ontology).
```
eg.
python main.py --id=GO:0000002 ../go-basic.obo
```

See code [here](https://github.com/moonstarsky37/article-beginner-webserver/tree/gh-pages/obo_relationships)
## To be continue...
