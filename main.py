# -*- coding: utf-8 -*-
"""Copy of Copy of Short text analysis Topic.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MgaFy6q55UZWtbwStesaXs0S8udhymMd
"""

import re
from collections import Counter
from pprint import pprint

import gensim
import gensim.corpora as corpora
import matplotlib.colors as mcolors
import nltk
import numpy as np
import pandas as pd
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
from gensim.utils import simple_preprocess
from matplotlib import pyplot as plt
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn import manifold  # multidimensional scaling
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics import pairwise_distances  # jaccard diss.
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import normalize
from wordcloud import WordCloud

data_title = pd.read_excel("title_stack.xlsx")  # read the dataset

"""## **LDA (Latent dirichlet allocation)**"""

data_title.head()

"""**Data Preprocessing**

Remove punctuation/single characters/lower casing
"""

stemmer = WordNetLemmatizer()


def clean_text(text):
    """Make text lowercase, remove text in square brackets,remove links,remove punctuation
    and remove words containing numbers."""
    text = str(text).lower()
    text = re.sub('[.*?]', '', text)
    # text = re.sub('https?://\S+|www\.\S+', '', text)

    # Removing link
    url_pattern = r'((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?'
    text = re.sub(url_pattern, ' ', text)

    text = re.sub('<.*?>+', '', text)
    # text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    # Remove all the special characters
    text = re.sub(r'\W', ' ', text)

    # remove all single characters
    text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)

    # Remove single characters from the start
    text = re.sub(r'\^[a-zA-Z]\s+', ' ', text)

    # Substituting multiple spaces with single space
    text = re.sub(r'\s+', ' ', text, flags=re.I)

    text = re.sub('\n', '', text)
    text = re.sub('w*dw*', '', text)

    # Lemmatization
    # text = text.split()

    # text = [stemmer.lemmatize(word) for word in text]
    # text = ' '.join(text)
    return text


data_title['new_title'] = data_title['title'].apply(clean_text)

"""**Prepare text for LDA analysis**"""

nltk.download('stopwords')

stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])


def sent_to_words(sentences):
    for sentence in sentences:
        # deacc=True removes punctuations
        yield gensim.utils.simple_preprocess(str(sentence), deacc=True)


def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc))
             if word not in stop_words] for doc in texts]


data = data_title.new_title.values.tolist()
data_words = list(sent_to_words(data))

# remove stop words
data_words = remove_stopwords(data_words)

# After removing stopwords
print(data_words[:2][:2])

# Create Dictionary
id2word = corpora.Dictionary(data_words)

# Create Corpus
texts = data_words

# Term Document Frequency
corpus = [id2word.doc2bow(text) for text in texts]

# View
print(corpus[:2][:2])

"""**LDA model tranining**"""

# It may took about 1.5 minutes to complete

# Build LDA model
lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                            id2word=id2word,
                                            num_topics=2,
                                            random_state=100,
                                            update_every=1,
                                            chunksize=10,
                                            passes=10,
                                            alpha='symmetric',
                                            iterations=100,
                                            per_word_topics=True)

# Print the Keyword in the 2 topics
pprint(lda_model.print_topics())
# doc_lda = lda_model[corpus]
# 0 -->Topic 1
# 1 -->Topic 2

"""Top 500 words"""
# Join the different processed titles together.
long_string = ','.join(list(data_title['new_title'].values))

# Create a WordCloud object
wordcloud = WordCloud(width=800, height=400, background_color="white", max_words=500, contour_width=3,
                      contour_color='steelblue')

# Generate a word cloud
wordcloud.generate(long_string)

# Visualize the word cloud
wordcloud.to_image()

"""**What is the Dominant topic and its percentage contribution in each document?**

In LDA models, each document is composed of multiple topics.
But, typically only one of the topics is dominant.
The below code extracts this dominant topic for each sentence and shows the weight of the topic and 
the keywords in a nicely formatted output.

This way, you will know which document belongs predominantly to which topic.
"""


# about 1 min required to run

def format_topics_sentences(ldamodel=None, corpus=corpus, texts=data):
    # Init output
    sent_topics_df = pd.DataFrame()

    # Get main topic in each document
    for i, row_list in enumerate(ldamodel[corpus]):
        row = row_list[0] if ldamodel.per_word_topics else row_list
        # print(row)
        row = sorted(row, key=lambda x: (x[1]), reverse=True)
        # Get the Dominant topic, Perc Contribution and Keywords for each document
        for j, (topic_num, prop_topic) in enumerate(row):
            if j == 0:  # => dominant topic
                wp = ldamodel.show_topic(topic_num)
                topic_keywords = ", ".join([word for word, prop in wp])
                sent_topics_df = sent_topics_df.append(
                    pd.Series([int(topic_num), round(prop_topic, 4), topic_keywords]), ignore_index=True)
            else:
                break
    sent_topics_df.columns = ['Dominant_Topic', 'Perc_Contribution', 'Topic_Keywords']

    # Add original text to the end of the output
    contents = pd.Series(texts)
    sent_topics_df = pd.concat([sent_topics_df, contents], axis=1)
    return sent_topics_df


df_topic_sents_keywords = format_topics_sentences(ldamodel=lda_model, corpus=corpus, texts=data_words)

# Format
df_dominant_topic = df_topic_sents_keywords.reset_index()
df_dominant_topic.columns = ['Document_No', 'Dominant_Topic', 'Topic_Perc_Contrib', 'Keywords', 'Text']
df_dominant_topic.head(10)

df_dominant_topic['Dominant_Topic'].unique()

"""## **Word Clouds of Top N Keywords in Each Topic:**

Though you’ve already seen what are the topic keywords in each topic,
a word cloud with the size of the words proportional to the weight is a pleasant sight.
The coloring of the topics I’ve taken here is followed in the subsequent plots as well.
"""

# 1. Wordcloud of Top N words in each topic

cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]  # more colors: 'mcolors.XKCD_COLORS'

cloud = WordCloud(stopwords=stop_words,
                  background_color='white',
                  width=2500,
                  height=1800,
                  max_words=10,
                  colormap='tab10',
                  color_func=lambda *args, **kwargs: cols[i],
                  prefer_horizontal=1.0)

topics = lda_model.show_topics(formatted=False)

fig, axes = plt.subplots(1, 2, figsize=(10, 10), sharex="all", sharey="all")

for i, ax in enumerate(axes.flatten()):
    fig.add_subplot(ax)
    topic_words = dict(topics[i][1])
    cloud.generate_from_frequencies(topic_words, max_font_size=300)
    plt.gca().imshow(cloud)
    plt.gca().set_title('Topic ' + str(i), fontdict=dict(size=16))
    plt.gca().axis('off')

plt.subplots_adjust(wspace=0, hspace=0)
plt.axis('off')
plt.margins(x=0, y=0)
plt.tight_layout()
plt.show()

"""## **Word Counts of Topic Keywords:**

When it comes to the keywords in the topics, the importance (weights) of the keywords matters.
Along with that, how frequently the words have appeared in the documents is also interesting to look.

Let’s plot the word counts and the weights of each keyword in the same chart.

You want to keep an eye out on the words that occur in multiple topics and
the ones whose relative frequency is more than the weight.
Often such words turn out to be less important.
The chart I’ve drawn below is a result of adding several such words to
the stop words list in the beginning and re-running the training process.
"""

topics = lda_model.show_topics(formatted=False)
data_flat = [w for w_list in data_words for w in w_list]
counter = Counter(data_flat)

out = []
for i, topic in topics:
    for word, weight in topic:
        out.append([word, i, weight, counter[word]])

df = pd.DataFrame(out, columns=['word', 'topic_id', 'importance', 'word_count'])

# Plot Word Count and Weights of Topic Keywords
fig, axes = plt.subplots(1, 2, figsize=(16, 10), sharey="all", dpi=160)
cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]
for i, ax in enumerate(axes.flatten()):
    ax.bar(x='word', height="word_count", data=df.loc[df.topic_id == i, :], color=cols[i], width=0.5, alpha=0.3,
           label='Word Count')
    ax_twin = ax.twinx()
    ax_twin.bar(x='word', height="importance", data=df.loc[df.topic_id == i, :], color=cols[i], width=0.2,
                label='Weights')
    ax.set_ylabel('Word Count', color=cols[i])
    ax_twin.set_ylim(0, 0.030)
    ax.set_ylim(0, 3500)
    ax.set_title('Topic: ' + str(i), color=cols[i], fontsize=16)
    ax.tick_params(axis='y', left=False)
    ax.set_xticklabels(df.loc[df.topic_id == i, 'word'], rotation=30, horizontalalignment='right')
    ax.legend(loc='upper left')
    ax_twin.legend(loc='upper right')

fig.tight_layout(w_pad=2)
fig.suptitle('Word Count and Importance of Topic Keywords', fontsize=22, y=1.05)
plt.show()

"""## **DMM- GSDMM (Gibbs sampling algorithm for a Dirichlet Mixture Model)**"""

# from gsdmm import MovieGroupProcess


"""# **PCA**"""

documents = data_title['new_title']

y = df_dominant_topic['Dominant_Topic'].values

# If we use all features then session wil be crash due to all usage of RAM,
# but if you set GPU or TPU then you can increase features

tfidf_vectorizer = TfidfVectorizer(max_features=4500, min_df=15, max_df=0.7, stop_words=stopwords.words('english'))
X = tfidf_vectorizer.fit_transform(documents)

x_upd = pd.DataFrame(X.todense(), columns=tfidf_vectorizer.get_feature_names())

# Scaling the data to bring all the attributes to a comparable level
scaler = StandardScaler()
X_scaled = scaler.fit_transform(x_upd)

# Normalizing the data so that
# the data approximately follows a Gaussian distribution
X_normalized = normalize(X_scaled)
# Converting the numpy array into a pandas DataFrame
X_normalized = pd.DataFrame(X_normalized)

pca = PCA(n_components=2)
X_principal2 = pca.fit_transform(X_normalized)
X_principal2 = pd.DataFrame(X_principal2)
X_principal2.columns = ['P1', 'P2']
print(X_principal2.head())

scatter = plt.scatter(X_principal2.iloc[:, 0], X_principal2.iloc[:, 1], c=y)

# labeling x and y axes
plt.xlabel('First Principal Component')
plt.ylabel('Second Principal Component')

"""As you can see in figure data is start from negative values.
The data is scaled and have two principal componenet analysis that's why has values close to 0."""

"""## **t-SNE (Stochastic neighbour embedding)**"""

# It may take about 2 minutes.

# Get topic weights and dominant topics ------------

# cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]

# Get topic weights
topic_weights = []
for i, row_list in enumerate(lda_model[corpus]):
    topic_weights.append([w for i, w in row_list[0]])

# Array of topic weights
arr = pd.DataFrame(topic_weights).fillna(0).values

# Keep the well separated points (optional)
arr = arr[np.amax(arr, axis=1) > 0.35]

# Dominant topic number in each doc
topic_num = np.argmax(arr, axis=1)

# tSNE Dimension Reduction
tsne_model = TSNE(n_components=2, verbose=1, random_state=0, angle=.99, init='pca')
tsne_lda = tsne_model.fit_transform(arr)

# Plot the Topic Clusters using Bokeh
output_notebook()
n_topics = 2
mycolors = np.array([color for name, color in mcolors.TABLEAU_COLORS.items()])
plot = figure(title="t-SNE Clustering of {} LDA Topics".format(n_topics),
              plot_width=900, plot_height=500)
plot.scatter(x=tsne_lda[:, 0], y=tsne_lda[:, 1], color=mycolors[topic_num])
show(plot)

# import pyLDAvis.gensim
# pyLDAvis.enable_notebook()
# vis = pyLDAvis.gensim.prepare(lda_model, corpus, dictionary=lda_model.id2word)
# vis

"""## **MDS (Multi-dimensional scaling)**"""

topic_binary = np.random.randint(2, size=(100, 10))
print(topic_binary.shape)

dis_matrix = pairwise_distances(topic_binary, metric='jaccard')
print(dis_matrix.shape)

mds_model = manifold.MDS(n_components=2, random_state=123,
                         dissimilarity='precomputed')
mds_fit = mds_model.fit(dis_matrix)
mds_coords = mds_model.fit_transform(dis_matrix)

topic_names = ['fill', 'dataset', 'datatable', 'linq', 'query', 'resultset', 'page', 'collection']
plt.figure()
plt.scatter(mds_coords[:, 0], mds_coords[:, 1],
            facecolors='none', edgecolors='none')  # points in white (invisible)
labels = topic_names
for label, x, y in zip(labels, mds_coords[:, 0], mds_coords[:, 1]):
    plt.annotate(label, (x, y), xycoords='data')
plt.xlabel('First Dimension')
plt.ylabel('Second Dimension')
plt.title('Dissimilarity among Topic')
plt.show()

"""Imagining our dataset being true, they are telling us that 
resultset, datatable, and dataset are almost perfect substitutes, 
since they satisfy the same need (represented by the area on the graph). 
On the other side, linq lies in a very isolated area, 
meaning that it has no competition in terms of substitutes.
Note that all the empty areas represent potential needs which have not been satisfied yet. 
That’s why multidimensional scaling might be a very powerful tool to investigate 
whether there is room for intervention in some markets, whether there are opportunities that have not been sized yet.
"""

"""## **LDA (Linear discriminant analysis)**"""

X = X_scaled

y = df_dominant_topic['Dominant_Topic'].values

lda_model = LinearDiscriminantAnalysis()
X_lda = lda_model.fit_transform(X, y)

plt.xlabel('LDA1')
plt.ylabel('LDA2')
plt.scatter(
    x=X_lda[:], y=y
)

"""Our target variable are 0 and 1 which represents the topic. That's why visualization graph line is oon 0 and 1.

## **END**
"""
