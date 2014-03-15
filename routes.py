from utils import revIndex, query_str, query_str_vs
import time
from flask import Flask, render_template, redirect
from forms import QueryForm
import os
import json

app = Flask(__name__)
app.config.from_object('config')

doc_dict = dict()
posting = dict()
info = 'zero documents indexed'
q_res = list()
q_str = ''

#doc_dict, posting = revIndex('./docs/*.htm*')
rindex_file = 'rindex.dat'
docs_file = 'docsfile.dat'

print os.getcwd()

print os.path.exists(rindex_file) , os.path.exists(rindex_file)

@app.route('/',methods = ['GET', 'POST'])
def home():
    global q_str, doc_dict, posting, info, q_res
    if not (os.path.exists(rindex_file) and os.path.exists(docs_file)):
        ind_f = open(rindex_file, 'w')
        doc_f = open(docs_file, 'w') 
        createIndex()
        json.dump(doc_dict, doc_f)
        json.dump(posting, ind_f)
        doc_f.close()
        ind_f.close()
    else:
        ind_f = open(rindex_file)
        doc_f = open(docs_file) 
        d_dict = json.load(doc_f)
        doc_dict = { int(key):val for key,val in d_dict.items() }
        posting = json.load(ind_f)
        info = str(len(doc_dict)) + ' documents indexed with '\
                + str(len(posting)) + ' unique words'
        doc_f.close()
        ind_f.close()
        

    content = {'info':info, 'res':q_res}
    form = QueryForm()
    if form.validate_on_submit():
        q_str = form.queryid.data
        return redirect('/query')
    return render_template('home.html', 
                            content = content,
                            form = form)


def createIndex():
    global doc_dict, posting, info, q_res
    t = time.time()
    if len(doc_dict) == 0 :
        doc_dict, posting = revIndex('./docs/*.htm*')
    print 'indexing took ' + str(time.time()-t) + ' seconds'
    info = str(len(doc_dict)) + ' documents indexed with '\
            + str(len(posting)) + ' unique words'
    q_res = []
  

@app.route('/query')
def runQuery():
    global q_res, q_str
    t = time.time()
    print q_str
    low_q_str = q_str.lower()
    d_len = len(doc_dict)
    res = query_str_vs(posting, d_len, low_q_str)
    #res = query_str(posting, low_q_str)
    q_str = ''
    print 'query took ' + str(time.time()-t) + ' seconds'
    q_res = map(sanitize,res)
    return redirect('/')

#map functions
def sanitize(x):
  return doc_dict[x].split('/')[-1]

print __name__
if __name__ == '__main__' :
    app.run(debug=True)

