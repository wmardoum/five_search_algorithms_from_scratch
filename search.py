# -*- coding: utf-8 -*-
"""Copy of Copy of Copy of Search.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z_zqGl2Dti2yz_JMg_ifx7ceOI6ni2qR
"""

import nltk
import nltk.corpus
import nltk.stem
from nltk.stem import PorterStemmer
import nltk.tokenize
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
import time 
from nltk.corpus import stopwords
import re
from math import sqrt
from math import log

# doc_path = "/content/drive/MyDrive/NLP Project files/smaller_sample.txt"
doc_path = "/content/drive/MyDrive/NLP Project files/ohsumed.88-91"

"""Imports stopwords and punctuation"""
nltk.download("stopwords")
nltk.download('punkt')
# print(stopwords.words("english"))

stop_words = stopwords.words('english')
ps = PorterStemmer()

"""Read from the file"""
t = time.time()
with open(doc_path, "r") as text:
    raw_text = text.read()
elapsed = time.time() - t
print("Time to load data: ", elapsed)

def rl(x):
  return range(len(x))

def starttime():
  return time.time()

def endtime(t):
  print(time.time() - t)
  return

""" Split by .I new document indicator, remove stopwords, split by field, save doc number by index, combine fields that have searchable info,
remove punctuaion, lowercase the words, stem them, and place list of words in list with corresponding index to doc number list"""

def build_document_dictionary(raw_text):
  raw_doc_strings= raw_text.split("\n.I ")[1:]
  tokenized_documents = []
  doc_ids = []
  stop_words = set(stopwords.words('english'))
  for i in range(len(raw_doc_strings)-1):
    stop_words = set(stopwords.words('english'))
    text = raw_doc_strings[i].split("\n")
    #print()
    #if len(text) < 1:
    #print(text)
    
    #print("doc id:", doc_id)
    separators = [".U", ".S", ".M", ".T", ".P", ".W", ".A"]
    
    list_of_docfields_without_separators = []
    for i in rl(text):
      if text[i] not in separators:
        list_of_docfields_without_separators.append(text[i])

    doc_id = list_of_docfields_without_separators[1]
    content = []
    if len(list_of_docfields_without_separators) > 3:
      content.extend([list_of_docfields_without_separators[3]])
    if len(list_of_docfields_without_separators) > 4:
      content.extend([list_of_docfields_without_separators[4]])
    #print(list_of_docfields_without_separators)
    if len(list_of_docfields_without_separators) > 6:
      content.extend([list_of_docfields_without_separators[6]])
    content_processed = []
    for i in rl(content):
      depunc = re.sub(r'[^\w\s]', ' ', content[i])
      lowered_depunc = depunc.lower()
      word_tokens = word_tokenize(lowered_depunc)
      filtered = []
      #for i in word_tokens:
      filtered = [ps.stem(w) for w in word_tokens if not w.lower() in stop_words and len(w) > 1]
      #word_list = lowered_depunc.split()
      content_processed.extend(filtered)
    tokenized_documents.append(content_processed)
    doc_ids.append(doc_id)
  return tokenized_documents, doc_ids

t = time.time()
tokenized_documents, doc_ids = build_document_dictionary(raw_text)
print("Time to tokenize documents: ",time.time() - t)


del raw_text

"""Create inverted index"""
def invert_index(tokenized_documents):
  inverted_index = {}
  for i in rl(tokenized_documents):
    for j in rl(tokenized_documents[i]):
      if tokenized_documents[i][j] not in inverted_index:
        inverted_index[tokenized_documents[i][j]] = [[i,j]] 
      else:
        inverted_index[tokenized_documents[i][j]].append([i,j])
  return inverted_index

t = time.time()
inverted_index = invert_index(tokenized_documents)
print(time.time() - t)

"""Create inverted index as a dictionary for better search runtime during duplicate prevention"""
def invert_index_dictionary(tokenized_documents):
  inverted_index = {}
  for i in rl(tokenized_documents):
    for j in rl(tokenized_documents[i]):
      if tokenized_documents[i][j] not in inverted_index:
        inverted_index[tokenized_documents[i][j]] = {i : [j]} 
      else:
        if i not in inverted_index[tokenized_documents[i][j]]:
          inverted_index[tokenized_documents[i][j]][i] = [j]
        else:
          inverted_index[tokenized_documents[i][j]][i].append(j)
  return inverted_index

t = time.time()
inverted_index_dictionary = invert_index_dictionary(tokenized_documents)
print(time.time() - t)

with open("/content/drive/MyDrive/NLP Project files/query.ohsu.1-63", "r") as f:
  raw_queries = f.read()

"""Similar to build document dictionary, with different handling for indexes, and removing "year old" which was common and carries little information"""
def tokenize_queries(raw_queries):
  by_query = raw_queries.split("<top>")[1:]
  tokenized_queries = []
  query_numbers = []
  for i in rl(by_query):
    
    query_by_line = by_query[i].split("\n")[1:]
    query_number = query_by_line[0].split()[-1]
    conc_query = query_by_line[1] + " " + query_by_line[3]
    depunc = re.sub(r'[^\w\s]', ' ', conc_query)
    lowered_depunc = depunc.lower()
    word_tokens = word_tokenize(lowered_depunc)
    #print(word_tokens)
    filtered = []
    #for i in word_tokens:
    filtered = [ps.stem(w) for w in word_tokens if not w.lower() in stop_words and len(w) > 1 and w.lower() not in ("title", "year", "old", "yo")]
    tokenized_queries.append(filtered)
    query_numbers.append(query_number)
  return tokenized_queries, query_numbers

tokenized_queries, query_numbers = tokenize_queries(raw_queries)
# for i in tokenized_queries:
#   print(i)

def dict_to_len_sorted_array(document_counter, query_number):
  sorted_list = []
  for k in sorted(document_counter, key=lambda k: len(document_counter[k]), reverse=True):
    sorted_list.append([query_number, k, document_counter[k]])
  return sorted_list

"""Levarages inverted index to check which documents had the word in it, then for each document, creates a list of words from the query
that are in the document. The document with the most words, regardless of frequency, is then ranked highest with dict_to_len_sorted_array
and returned as a search result."""
def return_boolean_results(tokenized_queries, inverted_index):
  sorted_results = []
  for j in rl(tokenized_queries):
    query = tokenized_queries[j]
    document_counter = {}
    for word in rl(query):
      if query[word] in inverted_index:
        doclist_by_word = inverted_index[query[word]]
        for i in doclist_by_word: 
          if i[0] not in document_counter:
            document_counter[i[0]] = [query[word]]
          else:
            if query[word] not in document_counter[i[0]]:
              document_counter[i[0]].append(query[word]) 
    """ compute percent of words used """
    victorovna = dict_to_len_sorted_array(document_counter,j)
    # print(victorovna)
    
    #print([len(victorovna[1][2])/len(tokenized_queries[0])])
    for k in rl(victorovna):
      victorovna[k].extend([len(victorovna[k][2])/len(tokenized_queries[j])]) #two static
    # print(victorovna)
    sorted_results.append(victorovna)
    """take out between comments if it breaks the code and uncomment below"""

    # sorted_results.append(dict_to_len_sorted_array(document_counter, j)
  return sorted_results

t = starttime()
sorted_boolean = return_boolean_results(tokenized_queries, inverted_index)
print("Time for boolean search:")
endtime(t)
""" 
Quick recap: Query id and tokenized queries should have consistent indexes
Same with doc_id and tokenized_documents : consistent indexes
indexes of sorted_boolean are [[Query index (for id and tokenized), document_score]][Doc index][list of included words][Score!]
"""
#Should give each document a score

del inverted_index

"""returns number of documents that have a given word in the inverted index for later use in IDF"""
def num_docs_dict_generate(inverted_index_dictionary):
  number_of_docs_containing_word = {}
  for i in inverted_index_dictionary:
    found_word = ""
    number_of_docs_containing_word[i] = 0
    for j in inverted_index_dictionary[i]:
      number_of_docs_containing_word[i] +=1
      # found_word = inverted_index[i][j][0]  
  return number_of_docs_containing_word

t = starttime()
number_of_docs_containing_word = num_docs_dict_generate(inverted_index_dictionary)
endtime(t)
# for i in number_of_docs_containing_word:
#   print(i, number_of_docs_containing_word[i])

"""Counts occurrences of a given word in every document for tf use later"""
def generate_word_counts_by_document(tokenized_documents):
  tf_by_doc_word = []
  for i in rl(tokenized_documents):
    doc_word_tf = {}
    for j in rl(tokenized_documents[i]):
      if tokenized_documents[i][j] not in doc_word_tf:
        doc_word_tf[tokenized_documents[i][j]] = 1
      else:
        doc_word_tf[tokenized_documents[i][j]] += 1
    tf_by_doc_word.append(doc_word_tf)
  return tf_by_doc_word

#print(tokenized_documents[0])

t = starttime()
tf_by_doc_word = generate_word_counts_by_document(tokenized_documents)
print("Time to generate document wordcounts")
endtime(t)

"""Generates the normalized TF vectors"""
def tokenized_to_tfs(tf_by_doc_word): 
  vector_lengths = []
  for i in rl(tf_by_doc_word):
    sum = 0
    for j in tf_by_doc_word[i]:
      sum += tf_by_doc_word[i][j] ** 2
    vector_lengths.append(sqrt(sum)) #Takes the root sum squared
  # print(vector_lengths)
  normalized_tf_docs_by_word = []
  for i in rl(tf_by_doc_word):
    normalized_tf_by_doc = {}
    for j in tf_by_doc_word[i]:
      normalized_tf_by_doc[j] = tf_by_doc_word[i][j] / vector_lengths[i]
    normalized_tf_docs_by_word.append(normalized_tf_by_doc)
  return normalized_tf_docs_by_word

t = starttime()
doc_tfs = tokenized_to_tfs(tf_by_doc_word)

tf_by_query_word = generate_word_counts_by_document(tokenized_queries)
query_tfs = tokenized_to_tfs(tf_by_query_word)
print("Time to generate TFs")
endtime(t)

def generate_idfs(doc_ids, number_of_docs_containing_word):
  numdocs = len(doc_ids)
  dfs = {}

  idfs = {}
  for i in number_of_docs_containing_word:
    #print(i, dfs[i])
    idfs[i] = log(numdocs/number_of_docs_containing_word[i])
  return idfs

idfs = generate_idfs(doc_ids, number_of_docs_containing_word)

"""Returns the search results as a string in the proper format for the trec_eval"""

#result_var = tf_scores_by_query_number
def output_log_file(result_var, run_type):
  log_file = ''
  for i in rl(result_var):
    for j in range(50):
      if j <= len(result_var[i]):
        log_file += str(query_numbers[i]) + '\tQ0\t' + str(doc_ids[result_var[i][j][1]]) + "\t" + str(j+1) + "\t" + str(result_var[i][j][0]) + "\t" + run_type + "\n"

  return log_file[:len(log_file)-2]

"""For each query, forms a list of documents which share a word with the query, then from that list of documents, takes the dot product of the 
TF vectors or IDF vectors respectively, stores that score in a list with their document index, and ranks by score."""

def search_by_tf_or_tfidf(query_tfs, doc_tfs, inverted_index_dictionary, use_idf=True):
  tf_scores_by_query_number = []
  for j in rl(query_tfs):
    query = query_tfs[j]
    doc_vec = []
    for word in query:
      if word in inverted_index_dictionary:  

        for w in inverted_index_dictionary[word]:
          #print("w:", w)
          #doc_vec.append(w)
          doc_vec.append(w)
    #print("doc_vec", doc_vec)
    scores = []
    checker_dict = {}
    for i in doc_vec:
      score = 0
      for word in query:
        if word in doc_tfs[i]:
          if use_idf == False:
            score += doc_tfs[i][word] * query[word]
          elif use_idf == True:
            score += doc_tfs[i][word] * query[word] * idfs[word] * idfs[word]
      #print(i, score)
      
      if i not in checker_dict:
        checker_dict[i] = score
        scores.append([score, i])
      # else:
      #   print("PREVENTED:", i)
    scorted = sorted(scores, reverse = True)
    tf_scores_by_query_number.append(scorted)
        #print(word, doc_tfs[doc_vec[i]])
  return tf_scores_by_query_number

dummy_dict = {}
dummy_dict[1]=2
1 in dummy_dict

t = starttime()
tf_scores_by_query_number = search_by_tf_or_tfidf(query_tfs, doc_tfs, inverted_index_dictionary, use_idf = False) 
print("TF Search time:")
endtime(t)

# for i in tf_scores_by_query_number:
#   print(i)

t = starttime()
#print(tf_scores_by_query_number[0])
tfidf_scored_by_query_number = search_by_tf_or_tfidf(query_tfs, doc_tfs, inverted_index_dictionary, use_idf = True)
print("TFIDF Search Time")
endtime(t)

# del tf_scores_by_query_number

boolean_results = []
for i in rl(sorted_boolean):
  query_results = []
  for j in rl(sorted_boolean[i]):
    query_results.append([sorted_boolean[i][j][3],sorted_boolean[i][j][1]])
  boolean_results.append(query_results)

# del sorted_boolean

"""Applies Rocchio's algorithm, assuming that the first five documents in the TFIDF search are relevant"""
def rocchios_algorithm(query_tfs, doc_tfs, tfidf_scored_by_query_number):
  ps_queries = query_tfs.copy()
  for queryx in rl(ps_queries):
    top5 = []
    for i in range(5):
      # if len(tfidf_scored_by_query_number[queryx]) < i:
      print(tfidf_scored_by_query_number[queryx][i][1])
      top5.append(tfidf_scored_by_query_number[queryx][i][1])
    for i in top5:
      top5_doc_vector_dict = doc_tfs[i]
      for word in top5_doc_vector_dict:
        if word in ps_queries[queryx]:
          ps_queries[queryx][word] += top5_doc_vector_dict[word]/3
        else:
          ps_queries[queryx][word] = top5_doc_vector_dict[word]/3
  return ps_queries

ps_queries = rocchios_algorithm(query_tfs, doc_tfs, tfidf_scored_by_query_number)
for i in ps_queries[0]:
  print(i)

t = time.time()
pseudo_relevant_results = search_by_tf_or_tfidf(ps_queries, doc_tfs, inverted_index_dictionary)
elapsed = time.time() - t
print(elapsed)

# del pseudo_relevant_results

inverted_query_index_dict = invert_index_dictionary(tokenized_queries)

"""For each word in a query, forms a list of the following five words. Then, while scoring, if any of the following five words in the document it's being
compared against is one of the five words pulled from the query, doubles score of the word being compared and also adds the score of the following word. 
This has the effect of preserving some of the importance of phrasing and word order."""
def search_by_tf_or_tfidf_with_word_order(query_tfs, doc_tfs, inverted_index_dictionary, tokenized_queries, inverted_query_index_dict, use_idf=True):
  tf_scores_by_query_number = []
  
  for j in rl(query_tfs):
    ranked_docs = {}
    query = query_tfs[j]
    following_words = {}
    for first_wordx in rl(tokenized_queries[j]):
      for k in range(5):
        l = k+1
        if len(tokenized_queries[j]) > first_wordx + l:
          if tokenized_queries[j][first_wordx] not in following_words:
            following_words[tokenized_queries[j][first_wordx]] = [tokenized_queries[j][first_wordx+l]]
          else: 
            following_words[tokenized_queries[j][first_wordx]].append(tokenized_queries[j][first_wordx+l])
    doc_vec = []
    for word in query:
      if word in inverted_index_dictionary:  
        #print(word)
        for w in inverted_index_dictionary[word]:
          #print(w)
          doc_vec.append(w)
    #print(doc_vec)
    scores = []
    for i in doc_vec:
      score = 0
      for word in query:
        following_words_have_been_verified = False
        if word in doc_tfs[i]:
          if use_idf == False:
            score += doc_tfs[i][word] * query[word]
          elif use_idf == True:
            if word in inverted_index_dictionary:
              if i in inverted_index_dictionary[word]:
                verified_following_word_list = []
                locations_in_doc = inverted_index_dictionary[word][i]
                if word in following_words:
                  for following_word in following_words[word]:
                    if following_word in inverted_index_dictionary:
                      if i in inverted_index_dictionary[following_word]:
                        following_word_indexes_in_doc = inverted_index_dictionary[following_word][i]
                        for following_word_index in following_word_indexes_in_doc:
                          for orig_word_loc_in_doc in locations_in_doc:
                            if following_word_index - orig_word_loc_in_doc < 5 and following_word not in verified_following_word_list:
                              following_words_have_been_verified = True
                              verified_following_word_list.append(following_word)
            if following_words_have_been_verified != True:
              score += doc_tfs[i][word] * query[word] * idfs[word] * idfs[word]
            elif following_words_have_been_verified:
              score += 2 * (doc_tfs[i][word] * query[word] * idfs[word] * idfs[word])
              for verified_following_word in verified_following_word_list:
                score += doc_tfs[i][verified_following_word] * query[verified_following_word] * idfs[verified_following_word] * idfs[verified_following_word]
      if i not in ranked_docs:
        ranked_docs[i] = score
        scores.append([score, i])
    scorted = sorted(scores, reverse = True)
    tf_scores_by_query_number.append(scorted)
        #print(word, doc_tfs[doc_vec[i]])
  return tf_scores_by_query_number

t = starttime()
custom_alg_results = search_by_tf_or_tfidf_with_word_order(query_tfs, doc_tfs, inverted_index_dictionary, tokenized_queries, inverted_query_index_dict, use_idf=True)
endtime(t)



"""Saves logs in the proper format"""

boolean_log = output_log_file(boolean_results, "boolean")
with open("aaboolean", "w") as file:
  file.write(boolean_log)

tf_log = output_log_file(tf_scores_by_query_number, "tf")
with open("aatf", "w") as file:
  file.write(tf_log)

tfidf_log = output_log_file(tfidf_scored_by_query_number, "tfidf")
with open("aatfidf", "w") as file:
  file.write(tfidf_log)

relevance_log = output_log_file(pseudo_relevant_results, "relevance_feedback")
with open("apsr", "w") as file:
  file.write(relevance_log)

custom_log = output_log_file(custom_alg_results, "proximity")
with open("aacustom", "w") as file:
  file.write(custom_log)
