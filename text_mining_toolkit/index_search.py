# module for indexing a corpus, and basic search

# glob module for finding files that match a pattern
import glob
# import os file deletion
import os
# import collections for index
import collections
# import hdf5 large dataset storage support
import h5py
# import pandas for index dataframe
import pandas
# import numpy for maths functions
import numpy
import numpy.lib.recfunctions
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
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    if os.path.isfile(wordcount_index_file):
        os.remove(wordcount_index_file)
        print("removed wordcount index file: ", wordcount_index_file)
        pass

    # delete relevance index
    relevance_index_file = content_directory + "index_relevance.hdf5"
    if os.path.isfile(relevance_index_file):
        os.remove(relevance_index_file)
        print("removed relevance index file: ", relevance_index_file)
        pass
    pass


# print existing index
def print_index2(content_directory):
    wordcount_index_file = content_directory + "index_wordcount.hdf5"

    with h5py.File(wordcount_index_file, 'r') as hf:
        wordcount_index_hf = hf.get('corpus_index')
        wordcount_index_np = numpy.array(wordcount_index_hf)
        pass

    print("wordcount_index_file ", wordcount_index_file)
    print(pandas.DataFrame(wordcount_index_np[:10], columns = wordcount_index_np.dtype.names))

    # relevance index
    #relevance_index_file = content_directory + "index_relevance.hdf5"
    #hd5_store2 = pandas.HDFStore(relevance_index_file, mode='r')
    #relevance_index = hd5_store2['corpus_index']
    #hd5_store2.close()
    #print("relevance_index_file ", relevance_index_file)
    #print(relevance_index.head(10))
    pass


# print existing index
def print_index(content_directory):
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    hd5_store1 = pandas.HDFStore(wordcount_index_file, mode='r')
    wordcount_index = hd5_store1['corpus_index']
    hd5_store1.close()
    print("wordcount_index_file ", wordcount_index_file)
    print(wordcount_index.head(10))

    # relevance index
    relevance_index_file = content_directory + "index_relevance.hdf5"
    hd5_store2 = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store2['corpus_index']
    hd5_store2.close()
    print("relevance_index_file ", relevance_index_file)
    print(relevance_index.head(10))
    pass


# create word count index just for one document
def create_wordcount_index_for_document2(content_directory, document_name, doc_words_list):
    # create index
    # (word, [document_name]) dictionary, there can be many [document_names] in list
    words_ctr = collections.Counter(doc_words_list)

    # convert to numpy structured array, ready for hdf5 storage
    names = ['word', document_name]
    formats = ['S20', 'i4']
    wordcount_index_np = numpy.fromiter(words_ctr.items(), dtype=dict(names=names, formats=formats))

    # finally save index
    wordcount_index_file = content_directory + document_name + "_index_wordcount.hdf5"
    with h5py.File(wordcount_index_file, 'w') as hf:
        hf.create_dataset('doc_index', data=wordcount_index_np)
        pass
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
    wordcount_index_file = content_directory + document_name + "_index_wordcount.hdf5"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='w')
    hd5_store['doc_index'] = wordcount_index
    hd5_store.close()
    pass


# merge document indices into a single index for the corpus
def merge_wordcount_indices_for_corpus2(content_directory):
    # start with empty list of arrays
    list_of_arrays = []

    # list of text files
    list_of_index_files = glob.glob(content_directory + "*_index_wordcount.hdf5")

    # load each index file and merge into accummulating corpus index
    for document_index_file in list_of_index_files:
        with h5py.File(document_index_file, 'r') as hf:
            temporary_document_index_hf = hf.get('doc_index')
            temporary_document_index_np = numpy.array(temporary_document_index_hf)
            pass

        # append document index to list for merging later
        list_of_arrays.append(temporary_document_index_np)

        # remove document index after merging
        #os.remove(document_index_file)
        pass

    # merge arrays in list
    wordcount_index_np = list_of_arrays[0]
    for a in list_of_arrays[1:]:
        wordcount_index_np = numpy.lib.recfunctions.join_by('word', wordcount_index_np, a, jointype='outer', usemask=True)
        pass

    wordcount_index_np.fill_value = 0
    wordcount_index_np = wordcount_index_np.filled()
    print(wordcount_index_np)

    # finally save index
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    with h5py.File(wordcount_index_file, 'w') as hf:
        hf.create_dataset('corpus_index', data=wordcount_index_np)
        pass
    pass


# merge document indices into a single index for the corpus
def merge_wordcount_indices_for_corpus(content_directory):
    # start with empty index
    wordcount_index = pandas.DataFrame()

    # list of text files
    list_of_index_files = glob.glob(content_directory + "*_index_wordcount.hdf5")

    # load each index file and merge into accummulating corpus index
    for document_index_file in list_of_index_files:
        hd5_store = pandas.HDFStore(document_index_file, mode='r')
        temporary_document_index  = hd5_store['doc_index']
        hd5_store.close()

        # following is a workaround for a pandas bug
        temporary_document_index.index = temporary_document_index.index.astype(str)

        wordcount_index = pandas.merge(wordcount_index, temporary_document_index, sort=False, how='outer', left_index=True, right_index=True)

        # remove document index after merging
        os.remove(document_index_file)
        pass

    # replace NaN wirh zeros
    wordcount_index.fillna(0, inplace=True)

    # finally save index
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    print("saving corpus word count index ... ", wordcount_index_file)
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='w')
    hd5_store['corpus_index'] = wordcount_index
    hd5_store.close()
    pass


# calculate relevance index from wordcount index
def calculate_relevance_index(content_directory):
    # load wordcount index
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='r')
    wordcount_index = hd5_store['corpus_index']
    hd5_store.close()

    # following is a workaround for a pandas bug
    wordcount_index.index = wordcount_index.index.astype(str)

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
    relevance_index_file = content_directory + "index_relevance.hdf5"
    print("saving corpus relevance index ... ", relevance_index_file)
    hd5_store = pandas.HDFStore(relevance_index_file, mode='w')
    hd5_store['corpus_index'] = frequency_index
    hd5_store.close()
    pass


# query wordcount index
def search_wordcount_index(content_directory, search_query):
    # load index if it already exists
    wordcount_index_file = content_directory + "index_wordcount.hdf5"
    hd5_store = pandas.HDFStore(wordcount_index_file, mode='r')
    wordcount_index = hd5_store['corpus_index']
    hd5_store.close()

    # following is a workaround for a pandas bug
    wordcount_index.index = wordcount_index.index.astype(str)

    # query string to list of search terms
    search_query_list = search_query.split()

    # do query
    documents = wordcount_index.loc[search_query_list]
    # sum the scores
    results = documents.sum()
    # multiply the scores
    #results = documents.prod()
    # filter out those with score of zero
    results = results[results > 0]
    return results.sort_values(ascending=False)


# query relevance index
def search_relevance_index(content_directory, search_query):
    # load index if it already exists
    relevance_index_file = content_directory + "index_relevance.hdf5"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store['corpus_index']
    hd5_store.close()

    # following is a workaround for a pandas bug
    relevance_index.index = relevance_index.index.astype(str)

    # query string to list of search terms
    search_query_list = search_query.split()

    # do query
    documents = relevance_index.loc[search_query_list]
    # sum the scores
    results = documents.sum()
    # multiply the scores
    #results = documents.prod()
    # filter out those with score of zero
    results = results[results > 0]
    return results.sort_values(ascending=False)


# get words ordered by relevance (across all documents)
def get_words_by_relevance(content_directory):
    # load relevance index
    relevance_index_file = content_directory + "index_relevance.hdf5"
    hd5_store = pandas.HDFStore(relevance_index_file, mode='r')
    relevance_index = hd5_store['corpus_index']
    hd5_store.close()

    # following is a workaround for a pandas bug
    relevance_index.index = relevance_index.index.astype(str)

    # sum the relevance scores for a word across all documents, sort
    word_relevance = relevance_index.sum(axis=1).sort_values(ascending=False)
    return word_relevance
