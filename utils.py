# Utility package for Inverted index, cosine similarity, boolean and vector space query methods 

from glob import glob
import string
import re
import time 
from math import sqrt, log

#dir_path = "./docs/*.htm*"


def revIndex(dir_path):
    ls_files = glob(dir_path)
    #create dictionary of file ientifiers
    doc_dict = {x:ls_files.index(x) for x in ls_files }

    #print doc_dict
    script_tag = re.compile('<script.*?<\/script>') #regex for removing script tags
    style_tag = re.compile('<style.*?<\/style>') #regex for removing style tags
    htm_tag = re.compile('<[^>]+>') #regex for removing html tags

    dict_postings = dict()

    for x in ls_files:
        content = file(x)
        post_script = re.sub(script_tag, '', content.read().replace('\n', ' '))
        post_style = re.sub(style_tag, '', post_script)
        post_tag = re.sub(htm_tag, '', post_style)
        post_sanity = strip_non_ascii(post_tag)
        post_sanity2 = string.lower(post_sanity.translate(string.maketrans('(){}[],-./;:=<>@|_','                  '), '\'!#$%&"*+?~' ))
    
        ls_words= post_sanity2.split()
        ls_words.sort()
        #postings structure is as follows
        #{ 'word':[ [total_doc_countt,total_freq], [doc_id1,..], [freq_in_doc1,..], [tf-idf_of_doc1,..] ] }
        unique_words = {y:ls_words.count(y) for y in ls_words}
        for (k,v) in unique_words.items():
            if k in dict_postings:
                it = dict_postings[k]
                it[0][0] = it[0][0] + 1
                it[0][1] = it[0][1] + v
                it[1].append(doc_dict[x])
                it[2].append(v)
                it[3].append(0)
                dict_postings[k] = it
            else:
                it = list()
                it.append( [1,v])
                it.append([doc_dict[x]])
                it.append([v])
                it.append([0])
                dict_postings[k] = it

    #populate the tf-idf for each document, term-wise
    post = update_tf_idf(dict_postings, len(doc_dict)) 
    return {y:strip_non_ascii(x) for x,y in doc_dict.items() }, post

# Query string using boolean model
def query_str(postings, quer_str):
    q_ls = quer_str.split();
    # List to hold the list of documents for each query term
    res_ls = list()

    for x in q_ls:
        if x in postings.keys():
            res_ls.append(postings[x][1])
    
    if len(res_ls) == 0 :
        return res_ls;
 
    # create to set by appending the list of documents and perform the union 
    res_st = set(res_ls[0])
    for x in res_ls:
        res_st.intersection_update(set(x))  
  
    return list(res_st)

# Simple non-ascii stripper  
def strip_non_ascii(str):
    stripped = (c for c in str if 0 < ord(c) < 127)
    return ''.join(stripped)

def remove_punctuation(str):
    punc = '\'!#$%&"*+?~'
    stripped = (c for c in str if c not in punc)
    return ''.join(stripped)

# Reduce function for computing the vector size
def add(x,y):
    return x+y

# Map function for computing the vector size
def square(x):
    return x*x

# function to compute cosine similarity of unit vectors
def cosine_sim(vec1, vec2):
    res = 0.0
    # compute dot product
    for x,y in zip(vec1,vec2):
        res = res+ x*y
    #return result based on unit vectors  
    return round(res,4)

#compute the tf-idf for all documents in postings
def update_tf_idf(postings, N):
    index = 0
    normalize_dict = dict()
    # TF-IDF for each document is computed term basis and stored in the same postings
    for k,v in postings.items():
        #print "posting for ",x, " is ", postings[x] 
        for x  in range(len(postings[k][1])) :
            postings[k][3][x] = log(N*1.0/postings[k][0][0],10) * postings[k][2][x]
            if postings[k][1][x] not in normalize_dict.keys():
                normalize_dict[postings[k][1][x]] = postings[k][3][x] * postings[k][3][x]
            else:
                normalize_dict[postings[k][1][x]] += postings[k][3][x] * postings[k][3][x]
   
    # normalization step
    normalize_dict = { k:sqrt(v) for k,v in normalize_dict.items() }  
    for k,v in postings.items():
        for x  in range(len(postings[k][1])) :
            postings[k][3][x] = postings[k][3][x] / normalize_dict[postings[k][1][x]]

    return postings


# Query using vector space model
def query_str_vs(postings, N, quer_str):
    ls = quer_str.split();
    # create the query term vector, consider only those terms in the postings
    q_ls = [x for x in ls if x in postings.keys()]
    unique_terms = {y:q_ls.count(y) for y in q_ls}
    term_vec = list()

    vec_sum = 0
    # compute TF-IDF for query term vector
    for x,y in unique_terms.items():
        idf = log(N*1.0/postings[x][0][0],10)
        term_vec.append(y*idf)
        vec_sum += y*idf * y*idf  

    for x in range(len(term_vec)):
        term_vec[x] = term_vec[x]/sqrt(vec_sum)

    #print "unique terms ", unique_terms
    #print "term_vec: ", term_vec

    # for each relevant document we need to compute TF-IDF. only for the terms in query.
    doc_set = set()
    empty_ls = list()
    for x in unique_terms.keys():
        doc_set.update(set(postings[x][1])) # set of documents which contain query terms
        empty_ls.append(0) # list with 0 value for each query term

    #for each relevant document create a null vector
    doc_vec = { x:list(empty_ls) for x in doc_set }
    index = 0

    # dynamically compute the TF-IDF vector for each document in the set
    for x in unique_terms.keys():
        #print "posting for ",x, " is ", postings[x] 
        for doc_id, tf_idf in zip(postings[x][1], postings[x][3]):
            doc_vec[doc_id][index] = tf_idf
        index+=1
        
    #print "doc_vec: ", doc_vec
    # now we have the TF-IDF for both term and document vectors
    # compute the cosine similarity
    res_ls = dict()
    for x,y in doc_vec.items():
        res_ls[x] = cosine_sim(term_vec,y)
  
    print "cosine sim: ", res_ls
    # need to sort the documents based on the cosine sim value before returning
    sorted_ls = [x[0] for x in sorted(res_ls.items(), key= lambda x:x[1], reverse=True)]
    #print sorted_ls 
    return sorted_ls

# Testing
#t = time.time()
#doc, post = revIndex("./test/*.htm*")
#print 'Indexing took ', time.time()-t, ' seconds'
#print "documents dict ", doc
#print "postings ", post
#doc_ls = query_str_vs(post,4, 'gold silver truck')
#for x in doc_ls:
#    print doc[x]

