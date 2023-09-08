# Imports
import nltk
import nltk.data
import re
import spacy
import pandas as pd
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
nltk.download('stopwords')
from spacy.lang.en import English

# Class initializations
nlp = spacy.load('en_core_web_sm')
lemmatizer = WordNetLemmatizer()

# List to hold all input sentences
sentences = []

# Dictionary to hold sentences corresponding to respective discourse markers
disc_sentences = {}

# Remaining sentences which do not have discourse markers (To be used later to generate other kinds of questions)
nondisc_sentences = []

# List of auxiliary verbs
aux_list = ['am', 'are', 'is', 'was', 'were', 'can', 'could', 'does', 'do', 'did', 'has', 'had', 'may', 'might', 'must',
            'need', 'ought', 'shall', 'should', 'will', 'would']

# List of all discourse markers
discourse_markers = ['because', 'as a result', 'since', 'when', 'although', 'for example', 'for instance', 'meanwhile','thus','by','where']

# Different question types possible for each discourse marker
qtype = {'because': ['Why'], 'since': ['When', 'Why'], 'when': ['When'], 'although': ['Yes/No'], 'as a result': ['Why'], 
        'for example': ['Give an example where'], 'for instance': ['Give an instance where'], 'to': ['Why'] , 
         'meanwhile': ['What was happening simultaneously when'],'thus':['How can','Why did'], 'by':['Who'], 'where':['Where','What']}

# The argument which forms a question
target_arg = {'because': 1, 'since': 1, 'when': 1, 'although': 1, 'as a result': 2, 'for example': 1, 'for instance': 1, 
              'to': 1,'meanwhile':1, 'thus':2, 'by':1, 'where':2}

# Function used to generate the questions from sentences which have already been pre-processed.
def generate_question(non_question_part,question_part, type):

    # Remove full stop and make first letter lower case
    question_part = question_part[0].lower() + question_part[1:]
    if(question_part[-1] == '.' or question_part[-1] == ','):
        question_part = question_part[:-1]
        
    # Capitalizing 'i' since 'I' is recognized by parsers appropriately    
    for i in range(0, len(question_part)):
        if(question_part[i] == 'i'):
            if((i == 0 and question_part[i+1] == ' ') or (question_part[i-1] == ' ' and question_part[i+1] == ' ')):
                question_part = question_part[:i] + 'I' + question_part[i + 1: ]
                
    if question_part.split()[0]=='since':
        question = ''.join(['Why'] + [question_part.split(',')[1]] + [' ?'])
        return question
    
    if question_part.split()[0]=='although':
        question_part = question_part.split(',')[1]
        type = 'Why'
                
    pattern = r"[,!:?]"
    question_part = re.sub(pattern, "", question_part)
    
    question = ""
    if(type == 'Give an example where' or type == 'Give an instance where' or type =='What was happening simultaneously when'):
        question = type + " " + question_part + '?'
        return question
    
    question = ""
    if(type == 'How can'):
        doc = nlp(non_question_part)
        for i, chunk in enumerate(doc.noun_chunks):
            if i == 0:
                sbj = chunk.text
                break
        question = type + " " + sbj.lower() + " " +question_part + '?'
        return question

    aux_verb = False
    res = None
    
    # Find out if auxiliary verb already exists
    for i in range(len(aux_list)):
        if(aux_list[i] in question_part.split()):
            aux_verb = True
            pos = i
            break

    # If auxiliary verb exists
    if(aux_verb):
        
        # Tokeninze the part of the sentence from which the question has to be made
        text = nltk.word_tokenize(question_part)
        tags = nltk.pos_tag(text)
        question_part = ""
        fP = False
        
        for word, tag in tags:
            if(word in ['I', 'We', 'we']):
                question_part += 'you' + " "
                fP = True
                continue
            question_part += word + " "

        # Split across the auxiliary verb and prepend it at the start of question part
        question = question_part.split(" " + aux_list[pos])
        if(fP):
             question = ["were "] + question
        else:
            question = [aux_list[pos] + " "] + question

        # If Yes/No, no need to introduce question phrase
        if(type == 'Yes/No'):
            question += ['?']
            
        elif(type != "non_disc"):
            question = [type + " "] + question + ["?"]
            
        else:
            question = question + ["?"]
         
        question = ''.join(question)

    # If auxilary verb does ot exist, it can only be some form of verb 'do'
    else:
        aux = None
        text = nltk.word_tokenize(question_part)
        tags = nltk.pos_tag(text)
        comb = ""

        '''There can be following combinations of nouns and verbs:
            NN/NNP and VBZ  -> Does
            NNS/NNPS(plural) and VBP -> Do
            NN/NNP and VBN -> Did
            NNS/NNPS(plural) and VBN -> Did
        '''
        
        for tag in tags:
            if(comb == ""):
                if(tag[1] == 'NN' or tag[1] == 'NNP'):
                    comb = 'NN'

                elif(tag[1] == 'NNS' or tag[1] == 'NNPS'):
                    comb = 'NNS'

                elif(tag[1] == 'PRP'):
                    if tag[0] in ['He','She','It']:
                        comb = 'PRPS'
                    else:
                        comb = 'PRPP'
                        tmp = question_part.split(" ")
                        tmp = tmp[1: ]
                        if(tag[0] in ['I', 'we', 'We']):
                            question_part = 'you ' + ' '.join(tmp)
                            
            if(res == None):
                res = re.match(r"VB*", tag[1])
                if(res):
                    
                    # Stem the verb
                    question_part = question_part.replace(tag[0], lemmatizer.lemmatize(tag[0]))
                res = re.match(r"VBN", tag[1])
                res = re.match(r"VBD", tag[1])
                
        
        if(comb == 'NN'):
            aux = 'does'
            
        elif(comb == 'NNS'):
            aux = 'do'
            
        elif(comb == 'PRPS'):
            aux = 'does'
            
        elif(comb == 'PRPP'):
            aux = 'do'
            
        if(res and res.group() in ['VBD', 'VBN']):
            aux = 'did'

        if(aux):
            if(type == "non_disc" or type == "Yes/No"):
                question = aux + " " + question_part + "?"
            else:
                question = type + " " + aux + " " + question_part + " ?"
    if(question != ""):
        question = question[0].upper() + question[1:]
    return question

# This function is used to get the named entities
def get_named_entities(sent):
    doc = nlp(sent)
    named_entities = [(X.text, X.label_) for X in doc.ents]

    return named_entities

# This function is used to get the required wh word
def get_wh_word(entity, sent):
    wh_word = ""
    if entity[1] in ['TIME', 'DATE']:
        wh_word = 'When'
        
    elif entity[1] == ['PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
        wh_word = 'What'
        
    elif entity[1] in ['PERSON']:
        wh_word = 'Who'
        
    elif entity[1] in ['PERCENT', 'MONEY', 'QUANTITY']:
        wh_word = 'How much'
        
    elif entity[1] in ['ORDINAL']:
        wh_word = 'Which'
        
    elif entity[1] in ['CARDINAL']:
        wh_word = 'How many'  
        
    elif entity[1] in ['GPE', 'LOC']:
        wh_word = 'Where'
        
    elif entity[1] in ['NORP', 'FAC' ,'ORG']:
        index = sent.find(entity[0])
        if index == 0:
            wh_word = "Who"            
        else:
            wh_word = "Where"            
    else:
        wh_word = "What"
    return wh_word

# This function generate questions based on NER templates
def generate_one_word_questions(sent):
    named_entities = get_named_entities(sent)
    questions = []

    if not named_entities:
        return questions
    
    for entity in named_entities:
        wh_word = get_wh_word(entity, sent)
        
        
        if(sent[-1] == '.'):
            sent = sent[:-1]
        
        if sent.find(entity[0]) == 0:
            questions.append(sent.replace(entity[0],wh_word) + '?')
            continue
       
        question = ""
        aux_verb = False
        res = None

        for i in range(len(aux_list)):
            if(aux_list[i] in sent.split()):
                aux_verb = True
                pos = i
                break
            
        if not aux_verb:
            pos = 9

        text = nltk.word_tokenize(sent)
        tags = nltk.pos_tag(text)
        question_part = ""
        if wh_word == 'When':
            word_list = sent.split(entity[0])[0].split()
            if word_list[-1] in ['in', 'at', 'on']:
                question_part = " ".join(word_list[:-1])
            else:
                question_part = " ".join(word_list)
            
            qp_text = nltk.word_tokenize(question_part)
            qp_tags = nltk.pos_tag(qp_text)
            
            question_part = ""
            
            for i, grp in enumerate(qp_tags):
                word = grp[0]
                tag = grp[1]
                if(re.match("VB*", tag) and word not in aux_list):
                    question_part += WordNetLemmatizer().lemmatize(word,'v') + " "
                else:
                    question_part += word + " "
                
            if question_part[-1] == ' ':
                question_part = question_part[:-1]
            
        elif wh_word == 'Who':
            for i, grp in enumerate(tags):
                word = grp[0]
                tag = grp[1]
                if(re.match("VB*", tag) and word not in aux_list):
                    break
                question_part += word + " "  
                
        elif wh_word == 'Where':
            ner_tags = nltk.ne_chunk(nltk.pos_tag(text))
            for chunk in ner_tags:
                if hasattr(chunk, 'label') and chunk.label() == 'GPE':
                    question_part = " ".join(question_part.split()[:-1])+ " "
                    continue
                if isinstance(chunk, nltk.Tree):
                    words = [word for word, tag in chunk.leaves()]
                    question_part += " ".join(words) + " "
                else:
                    question_part += chunk[0] + " "
        else:
            for i, grp in enumerate(tags):                
                #Break the sentence after the first non-auxiliary verb
                word = grp[0]
                tag = grp[1]
                if(re.match("VB*", tag) and word not in aux_list):
                    question_part += word
                    if i<len(tags) and 'NN' not in tags[i+1][1] and wh_word != 'When':
                        question_part += " "+ tags[i+1][0]
                    break
                question_part += word + " "     
                
        pos_tags = nltk.pos_tag(nltk.word_tokenize(question_part))
        question_part = " ".join(word.lower() if tag in ["PRP", "PRP$"] else word for word, tag in pos_tags)
        
        question = question_part.split(" "+ aux_list[pos])
        question = [aux_list[pos] + " "] + question
        question = [wh_word+ " "] + question + ["?"]
        question = ''.join(question)
        questions.append(question)
    
    return questions        

# Function used to pre-process sentences which have discourse markers in them
def discourse():
    temp = []
    target = ""
    questions = []
    global disc_sentences
    disc_sentences = {}
    for i in range(len(sentences)):
        maxLen = 9999999
        val = -1
        for j in discourse_markers:
            tmp = len(sentences[i].split(j)[0].split(' '))  
            
            # To get valid, first discourse marker.   
            if(len(sentences[i].split(j)) > 1 and tmp >= 3 and tmp < maxLen):
                maxLen = tmp
                val = j
                
        if(val != -1):

            # To initialize a list for every new key
            if(disc_sentences.get(val, 'empty') == 'empty'):
                disc_sentences[val] = []
                
            disc_sentences[val].append(sentences[i])
            temp.append(sentences[i])


    nondisc_sentences = list(set(sentences) - set(temp))
    
    t = []
    for k, v in disc_sentences.items():
        for val in range(len(v)):
            
            # Split the sentence on discourse marker and identify the question part
            question_part = disc_sentences[k][val].split(k)[target_arg[k] - 1]
            non_question_part = disc_sentences[k][val].split(k)[target_arg[k]-2]
            
            q = generate_question(non_question_part,question_part, qtype[k][0])
            if(q != ""):
                questions.append([disc_sentences[k][val],q])
                
                
    for question_part in nondisc_sentences:
        s = "non_disc"
        sentence = question_part
        text = nltk.word_tokenize(question_part)
        if(text[0] == 'Yes'):
            question_part = question_part[5:]
            s = "Yes/No"
            
        elif(text[0] == 'No'):
            question_part = question_part[4:]
            s = "Yes/No"
            
        q = generate_question(0,question_part, s)
        if(q != ""):
            questions.append([sentence,q])
            
        if question_part.split()[0].lower() != 'although':
            l = generate_one_word_questions(question_part)
            questions += [[sentence,i] for i in l]
        
    return questions


def Blooms_levels(questions):
    stop_words = set(stopwords.words('english'))
    Level_1 = []
    Level_2 = []
    Level_3 = []
    Level_4 = []
    Level_5 = []
    Level_6 = []
    others = []
    
    for sentence in questions:
        words = sentence.split()
     
        if words[0].lower() == 'when':
            Level_1.append(" ".join(words))
            
            new_words = ['Give some inference about'] + [word for word in words[2:-1] ]+ ['.']
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
            new_words = ['What do you think that'] + [word for word in words[2:] ]
            new_sentence = " ".join(new_words)
            Level_6.append(new_sentence)
            
        elif words[0].lower() == 'where':
            Level_1.append(" ".join(words))
            
        elif words[0].lower() == 'how' and words[1].lower() == 'much':
            Level_1.append(" ".join(words))
            
        elif words[0].lower() == 'how' and words[1].lower() == 'many':
            Level_1.append(" ".join(words))
            
        elif words[0].lower() == 'why':
            Level_1.append(" ".join(words))            
            
            if words[1] == 'did' or words[1] == 'do' or words[1] == 'does':
                new_words = ['Analyze the reasons for'] + [word for word in words[2:-1]] + ['.']
            else:
                new_words = ['Analyze the reasons for'] + [word for word in words[1:-1]] + ['.']
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
            new_words = ['Evaluate the reasons'] + [word for word in words[:-1]] + ['. Were there any other options available ?']
            new_sentence = " ".join(new_words)
            Level_5.append(new_sentence)
            
        elif words[0].lower() == 'give' and words[2].lower() == 'example':
            Level_1.append(" ".join(words))
            
            new_words = ['Explain,'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_2.append(new_sentence)
            
            new_words = ['Show that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_3.append(new_sentence)
            
            new_words = ['Illustrate'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_3.append(new_sentence)
            
            new_words = ['Examine'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
            new_words = ['Analyze the possibilities that '] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
            new_words = ['Justify that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_5.append(new_sentence)
            
        elif words[0].lower() == 'give' and words[2].lower() == 'instance':
            Level_1.append(" ".join(words))
            
            new_words = ['Explain'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_2.append(new_sentence)
            
            new_words = ['Discuss the fact that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_2.append(new_sentence)  
            
            new_words = ['Show that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_3.append(new_sentence)
            
            new_words = ['Illustrate'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_3.append(new_sentence)
            
            new_words = ['Analyze the possibilities that '] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
            new_words = ['Justify that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_5.append(new_sentence)
            
            new_words = ['Validate that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_6.append(new_sentence)
            
            new_words = ['Hypothesize that'] + [word for word in words[4:-1] ] + ['.']
            new_sentence = " ".join(new_words)
            Level_6.append(new_sentence)
            
        elif words[0].lower() == 'what' and words[2].lower() == 'happening':
            Level_1.append(" ".join(words))
            
            new_words = ['What happened '] + [word for word in words[4:] ]
            new_sentence = " ".join(new_words)
            Level_2.append(new_sentence)
            
        elif words[0].lower() == 'how' and words[1].lower() == 'can':
            Level_1.append(" ".join(words))
            
            new_words = ['Why did'] + [word for word in words[2:] ]
            new_sentence = " ".join(new_words)
            Level_4.append(new_sentence)
            
        elif words[0].lower() == 'what':
            Level_1.append(" ".join(words))
            
            new_words = ['Define'] + [word for word in words[1:-1] if word.lower() not in stop_words] + ['.']
            new_sentence = " ".join(new_words)
            Level_1.append(new_sentence)
            
            new_words = ['Describe'] + [word for word in words[1:-1] if word.lower() not in stop_words] + ['.']
            new_sentence = " ".join(new_words)
            Level_1.append(new_sentence)
            
            new_words = ['Explain'] + [word for word in words[1:-1] if word.lower() not in stop_words] + ['.']
            new_sentence = " ".join(new_words)
            Level_2.append(new_sentence)
            
        elif words[0].lower() == 'who':
            Level_1.append(" ".join(words))   
            
            new_words = ['What was the significance of the person'] + [" ".join(words).lower()]
            new_sentence = " ".join(new_words)
            Level_5.append(new_sentence)         
        else:
            others.append(" ".join(words))
            
    Level_1 = list(set(Level_1))
    Level_2 = list(set(Level_2))
    Level_3 = list(set(Level_3))
    Level_4 = list(set(Level_4))
    Level_5 = list(set(Level_5))
    Level_6 = list(set(Level_6))
    others = list(set(others))
    return (Level_1, Level_2, Level_3, Level_4, Level_5, Level_6, others)

def generate_questions(data):
    global sentences
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(data)
    questions_answer_list = discourse()
    questions = []
    for pair in questions_answer_list:
        questions.append(pair[1])
    Q = Blooms_levels(questions)
    return Q

