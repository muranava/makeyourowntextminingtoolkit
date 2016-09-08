# module for indexing a corpus, and basic search

# glob module for finding files that match a pattern
import glob
# import os file deletion
import os
# import collections for index
import collections
# import pandas for index dataframe
import pandas
# import numpy for maths functions
import numpy
# max columns when printing .. (may not be needed if auto detected from display)
pandas.set_option('max_columns', 5)


# delete indices
def delete_indices(content_directory):
    # delete wordcount index
    """
    Deletes any existing index files from the corpus directory.
    Currently these are index.wordcount and index.relevance.

    :param content_directory: directory containing the text corpus, this should be CorpusReader.content_directory
    :type content_directory: string
    """
    wordcount_index_file = content_directory + "index.wordcount"
    if os.path.isfile(wordcount_index_file):
        os.remove(wordcount_index_file)
        print("removed wordcount index file: ", wordcount_index_file)
        pass

    # delete relevance index
    relevance_index_file = content_directory + "index.relevance"
    if os.path.isfile(relevance_index_file):
        os.remove(relevance_index_file)
        print("removed relevance index file: ", relevance_index_file)
        pass
    pass


# print existing index
def print_index(content_directory):
    # wordcount index
    """
    Prints the index files, and only a small section (max 10 rows, 5 cols) if the indices are large.
    Currently these are index.wordcount and index.relevance.

    :param content_directory: directory containing the text corpus, this should be CorpusReader.content_directory
    :type content_directory: string
    """
    wordcount_index_file = content_directory + "index.wordcount"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='r')
    wordcount_index = hd5_store['corpus_index']
    hd5_store.close()
    print("wordcount_index_file ", wordcount_index_file)
    print(wordcount_index.head(10))

    # relevance index
    relevance_index_file = content_directory + "index.relevance"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store['corpus_index']
    hd5_store.close()
    print("relevance_index_file ", relevance_index_file)
    print(relevance_index.head(10))
    pass


# create word count index just for one document
def create_wordcount_index_for_document(content_directory, document_name, doc_words_list):
    # start with empty index
    wordcount_index = pandas.DataFrame()

    # create index
    # (word, [document_name]) dictionary, there can be many [document_names] in list
    words_ctr = collections.Counter(doc_words_list)
    for w, c in words_ctr.items():
        #print("=== ", w, c)
        wordcount_index.ix[w, document_name] = c
        pass

    # replace NaN wirh zeros
    wordcount_index.fillna(0, inplace=True)

    # finally save index
    wordcount_index_file = content_directory + document_name + "_index.wordcount"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='w')
    hd5_store['doc_index'] = wordcount_index
    hd5_store.close()
    pass


# merge document indices into a single index for the corpus
def merge_wordcount_indices_for_corpus(content_directory):
    # start with empty index
    wordcount_index = pandas.DataFrame()

    # list of text files
    list_of_index_files = glob.glob(content_directory + "*_index.wordcount")

    # load each index file and merge into accummulating corpus index
    for document_index_file in list_of_index_files:
        #print("merging index file .. ", document_index_file)
        hd5_store = pandas.HDFStore(document_index_file, mode='r')
        temporary_document_index  = hd5_store['doc_index']
        hd5_store.close()
        wordcount_index = pandas.merge(wordcount_index, temporary_document_index, sort=False, how='outer', left_index=True, right_index=True)

        # remove document index after merging
        os.remove(document_index_file)
        pass

    # replace NaN wirh zeros
    wordcount_index.fillna(0, inplace=True)

    # finally save index
    wordcount_index_file = content_directory + "index.wordcount"
    print("saving corpus index ... ", wordcount_index_file)
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='w')
    hd5_store['corpus_index'] = wordcount_index
    hd5_store.close()
    pass


# calculate relevance index from wordcount index
def calculate_relevance_index(content_directory):
    # load wordcount index
    wordcount_index_file = content_directory + "index.wordcount"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='r')
    wordcount_index = hd5_store['corpus_index']
    hd5_store.close()

    # word frequency (per document) from wordcount, aka TF
    frequency_index = wordcount_index/wordcount_index.sum()

    # penalise short word length
    for word in frequency_index.index.values:
        frequency_index.loc[word] = frequency_index.loc[word] * numpy.tanh(len(word)/5.0)
        pass

    # inverse document frequency
    for word in frequency_index.index.values:
        documents = frequency_index.loc[word]
        matching_documents = documents[documents > 0]
        inverse_document_frequency = 1.0 - (len(matching_documents) / len(documents))
        # print("word =", word, " idf = ", inverse_document_frequency)
        frequency_index.loc[word] = frequency_index.loc[word] * inverse_document_frequency
        pass

    # save relevance index
    relevance_index_file = content_directory + "index.relevance"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='w')
    hd5_store['corpus_index'] = frequency_index
    hd5_store.close()
    pass


# query index
def search_index(content_directory, search_query):
    # load index if it already exists
    relevance_index_file = content_directory + "index.relevance"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store['corpus_index']
    hd5_store.close()


    # do query
    documents = relevance_index.loc[search_query]
    # filter out those with word count of zero
    matching_documents = documents[documents > 0]
    print("matching_documents", matching_documents)
    # to list
    matching_documents_list = [(k,v) for (k,v) in matching_documents.to_dict().items()]
    return matching_documents_list


# get words ordered by relevance (across all documents)
def get_words_by_relevance(content_directory):
    # load relevance index
    relevance_index_file = content_directory + "index.relevance"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store['corpus_index']
    hd5_store.close()

    # sum the relevance scores for a word across all documents, sort
    word_relevance = relevance_index.sum(axis=1).sort_values(ascending=False)
    # print(word_relevance)
    word_relevance_counter = collections.Counter(word_relevance.to_dict())
    # return collections.counter object
    return word_relevance_counter