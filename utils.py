#!/usr/bin/env python
# coding: utf-8

# In[ ]:
from __future__ import unicode_literals
from youtube_search import YoutubeSearch
import youtube_dl
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr
import bs4 as bs
import urllib.request
import re
import nltk
import heapq
from wit import Wit 
import json
import yagmail
import smtplib, ssl
import pubchempy as pcp
import json
import requests
import docx
from socket import gaierror



def wit_response(message_text):
    wit_access_token = "FE5AVTCKI4WL7X2S4RCZPS4L7D53S5QP"
    client = Wit(access_token = wit_access_token)
    resp = client.message(message_text)
    #res_string=json.dumps(resp)
    #rs_dict=json.loads(res_string)

    data_str=json.dumps(resp)
    data=json.loads(data_str)

    def depth(data):
        if "entities" in data:
            return 1 +  max([0] + list(map(depth, data['entities'])))      
        else:
            return 1
    levels_with_entities=depth(data)


    #print(json.dumps(data,indent=2,sort_keys=True))

    chemicals=[]
    number_entities=len(list(resp['entities']))
    intent=resp['intents'][0]['name']

    for i in range(number_entities):
        
        if list(resp['entities'].values())[i][0] and list(resp['entities'].values())[i][0]['entities']!=[]:
            
            if levels_with_entities>1:
                more_entities=len(list(resp['entities'].values())[i][0]['entities'])
                
                for e in range(more_entities):
                    chemical_label=list(resp['entities'].values())[i][0]['entities'][e]['name']
                    if chemical_label=="chemical_substance":
                        chemical_name=list(resp['entities'].values())[i][0]['value']
                        chemicals.append(chemical_name)
                        #print(chemicals)

        else:
            elements_entity=len(list(resp['entities'].values())[i])
            chemical=list(resp['entities'].values())[i][0]['name']
            
            chemic_name=list(resp['entities'].values())[i][0]['name']
            more_entities=list(resp['entities'].values())[i][0]['entities']
            if elements_entity>=1:    
                for y in range(elements_entity):
                    id_chemical=list(resp['entities'].values())[i][y]['name']
                    
                    if id_chemical=="chemical_substance":
                        name_chemical=list(resp['entities'].values())[i][y]['value']
                        chemicals.append(name_chemical)
                   
            else:
                if chemical=="chemical_substance":
                    chemical_name=list(resp['entities'].values())[i][0]['value']
                    chemicals.append(chemical_name)
                    #print(chemical_name)


    return (chemicals,intent)
    #entity = None
    #value = None
    
    #try:
    #    value = list(resp['entities'].values())[0][0]['value']
    #    entity = resp['intents'][0]['name']
    #except:
    #    pass
    #return (entity,value)

def handling_and_storage(chemical_compound,cid):

    API_ENDPOINT='https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'+str(cid)+'/JSON'   
    dat={}
        #print(newintent)
    headers = {'authorization': 'Bearer ','Content-Type': 'application/json'}
    resp=requests.post(API_ENDPOINT,headers=headers,json=dat)
    textt=json.loads(resp.content)   
    def json_extract(obj,key):
        
        arr=[]
        def extract(obj,arr,key):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if isinstance(v,(dict,list)):
                        extract(v,arr,key)
                    elif v==key:
                        arr.append(obj)
            elif isinstance(obj,list):
                for item in obj:
                    extract(item,arr,key)
            return (arr)
        values=extract(obj,arr,key)
        return values
    result_safe=json_extract(textt,'Information for Safe Storage')
    result_storage=json_extract(textt,'Information for Storage Conditions')
    #print(result_storage)

    handling_storage={}
    safe_storage={}
    for key,value in result_storage[0].items():
        if value not in handling_storage.values():
            handling_storage[key]=value

    for key,value in result_safe[0].items():
        if value not in safe_storage.values():
            safe_storage[key]=value
    #print(handling_storage)
    #print(json.dumps(handling_storage,indent=2,sort_keys=True))
    #print(handing_storage['Information'][0]['Value']['StringWithMarkup'][0]['String'])
    #print(handing_storage['Information'][0]['Value']['StringWithMarkup'][0]['String'])
    elements_storage=len(handling_storage['Information'])
    elements_safe=len(safe_storage['Information'])

    response_storage_res=""
    response_safe_res=""
    for i in range(elements_storage):
        
        response_storage=handling_storage['Information'][i]['Value']['StringWithMarkup'][0]['String']
        response_storage_res+=response_storage
        
    for x in range(elements_safe):  
        response_safe=safe_storage['Information'][x]['Value']['StringWithMarkup'][0]['String']
        response_safe_res+=response_safe
        #print("---",safe_storage['Information'][x]['Value']['StringWithMarkup'][0]['String'])
    response=response_storage_res+response_safe_res
    #print(response_storage_res,"----",response_safe_res)
    #print(response)
    return response
    chemical={}
    for chemical_compound in chemicals:
        for compound in pcp.get_compounds(chemical_compound,'name'):
            chemical['cid']=compound.cid
            chemical['molecular_formula']=compound.molecular_formula
            chemical['molecular_weight']=compound.molecular_weight
            chemical['isomeric_smiles']=compound.isomeric_smiles
            #cid=str(compound.cid)
    #print("--->",chemical_compound,chemical['cid'])
    response=handling_and_storage(chemical_compound,chemical['cid'])
    #print("--->",response)
    if response!="":

        receiver="contacto@numerica.mx"
        body="Hello, Buddy!"
        body+="This is an email with the information requested on the chat. Hope you find it hepful"
        yag=yagmail.SMTP("anunciosgibsa@gmail.com","VentaProduct51g")
        yag.send(to=receiver,
                subject="Summarized Documentation: "+chemical_compound.upper(),
                contents=response)
        response_api="Data Sent"
    else:
        response_api="Data Not Sent"     

    return response_api

def ghs_classification(chemical_compound,cid):

    API_ENDPOINT='https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'+str(cid)+'/JSON'   
    dat={}
    #print(newintent)
    headers = {'authorization': 'Bearer ','Content-Type': 'application/json'}
    resp=requests.post(API_ENDPOINT,headers=headers,json=dat)
    textt=json.loads(resp.content)   
    def json_extract(obj,key):
        
        arr=[]
        def extract(obj,arr,key):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if isinstance(v,(dict,list)):
                        extract(v,arr,key)
                    elif v==key:
                        arr.append(obj)
            elif isinstance(obj,list):
                for item in obj:
                    extract(item,arr,key)
            return (arr)
        values=extract(obj,arr,key)
        return values
    result=json_extract(textt,'Synonyms')
    #print(result)
    #print(json.dumps(result,indent=2,sort_keys=True))

    ghs_classification={}
    for key,value in result[0].items():
        if value not in ghs_classification.values():
            ghs_classification[key]=value

    #print(ghs_classification)        
    #print(json.dumps(result[0]['Section'][1]['Information'],indent=2,sort_keys=True))
    response_api=""
    response=''
    number_synonyms=len(ghs_classification['Section'][1]['Information'][0]['Value']['StringWithMarkup'])
    n_synonym=result[0]['Section'][1]['Information'][0]['Value']['StringWithMarkup']
    respone_api=''
    response_title=chemical_compound+' Synonyms:\n\n'
    for n in range(number_synonyms):
        #print(n_synonym[n]['String'])
        response=n_synonym[n]['String']+", "
        respone_api+=response
    response_result=response_title+respone_api
    #print(response_result)    
    
    return response_result
def toxicity_data(chemical_compound,cid):


    API_ENDPOINT='https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/'+str(cid)+'/JSON'   
    dat={}
    headers = {'authorization': 'Bearer ','Content-Type': 'application/json'}
    resp=requests.post(API_ENDPOINT,headers=headers,json=dat)
    textt=json.loads(resp.content)   
    def json_extract(obj,key):

        arr=[]
        def extract(obj,arr,key):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if isinstance(v,(dict,list)):
                        extract(v,arr,key)
                    elif v==key:
                        arr.append(obj)
            elif isinstance(obj,list):
                for item in obj:
                    extract(item,arr,key)
            return (arr)
        values=extract(obj,arr,key)
        return values
    result=json_extract(textt,'Toxicity Summary')

    toxicity={}
    for key,value in result[0].items():
        if value not in toxicity.values():
            toxicity[key]=value

    result_toxicity=toxicity['Information'][0]['Value']['StringWithMarkup'][0]['String']
    return result_toxicity

    

def send_email(usender_email,ureceiver_email,chemical_compound,response):
    
    port = 2525

    smtp_server = "smtp.mailtrap.io"
    login = "9685933e787454" # paste your login generated by Mailtrap
    password = "5b6e8179d6f09b" # paste your password generated by Mailtrap

    # specify the sender’s and receiver’s email addresses
    sender = usender_email
    receiver = ureceiver_email

    message = f"""\
    Subject: Hi Buddy! - Summarized Documentation
    To: {receiver}
    From: {sender}

    This is an email with the information requested on the chat. Hope you find it hepful\n\n\n"""+str(response).encode('utf-8')

    try:
        #send your message with credentials specified above
        with smtplib.SMTP(smtp_server, port) as server:
            server.login(login, password)
            server.sendmail(sender, receiver, message)

        # tell the script to report if your message was sent or which errors need to be fixed 
        response_api='Data Sent'
    except (gaierror, ConnectionRefusedError):
        print('Failed to connect to the server. Bad connection settings?')
        response_api='Data Not Sent'
    except smtplib.SMTPServerDisconnected:
        print('Failed to connect to the server. Wrong user/password?')
        response_api='Data Not Sent'
    except smtplib.SMTPException as e:
        print('SMTP error occurred: ' + str(e))
        response_api='Data Not Sent'
         
    return response_api

def transcribe_audio(keyword):
    max_elements=1
    #results=YoutubeSearch('Benzene',max_results=5).to_json()
    results=YoutubeSearch(keyword,max_results=max_elements).to_dict()
    #print(results)
    for i in range(max_elements):
        url="https://www.youtube.com/watch?v="+results[i]['id']
        title_video=results[i]['title']
        duration=results[i]['duration']
        views=results[i]['views']
        print('****************')
        print("Titulo:",title_video)
        print("Duration:",duration)
        print('Url:',url)
        print('Views:',views)
        print("***************")


        ydl_opts={
            'format':'bestaudio/best',
            'postprocessors': [{
                'key':'FFmpegExtractAudio',
                'preferredcodec':'wav',
                'preferredquality':'192',       
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url)
            fn = ydl.prepare_filename(info_dict)
            path=fn[:-4]+"wav"


    r=sr.Recognizer()
    print("started..")
    def get_large_audio_transcription(path):
        sound=AudioSegment.from_wav(path)
        chunks=split_on_silence(sound,
                                min_silence_len=500,
                                silence_thresh=sound.dBFS-14,
                                keep_silence=500,)
        folder_name="audio-chunks"
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        whole_text=""
        for i,audio_chunk in enumerate(chunks,start=1):
            chunk_filename=os.path.join(folder_name,f"chunk{i}.wav")
            audio_chunk.export(chunk_filename,format="wav")
            with sr.AudioFile(chunk_filename) as source:
                audio_listened=r.record(source)
              
                try:
                    text=r.recognize_google(audio_listened,language="en-US")
                except sr.UnknownValueError as e:
                    pass
                    #print("Error:",str(e))
                else:
                    text=f"{text.capitalize()}. "
                    #print(chunk_filename,":",text)
                    whole_text+=text

        return whole_text


    # (starting here:)#path="Audacity FFMpeg codec install for Windows-v2J6fT65Ydc.wav"
    #print("\nFull text:",get_large_audio_transcription(path))
    article_text=get_large_audio_transcription(path)

    article_text=re.sub(r'\[[0-9]*\]',' ',article_text)
    article_text=re.sub(r'\s+',' ',article_text)

    formatted_article_text=re.sub('^a-zA-Z',' ',article_text)
    formatted_article_text=re.sub(r'\s+',' ',formatted_article_text)

    #print(formatted_article_text)  #final text from audio

    print('*********************')
    print("Summaryzing..")
    #tokenization
    sentence_list=nltk.sent_tokenize(article_text)

    stopwords=nltk.corpus.stopwords.words('english')
    word_frequencies={}
    for word in nltk.word_tokenize(formatted_article_text):
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word]=1
            else:
                word_frequencies[word]+=1

    #print(list(map(str,word_frequencies)))

    #word frequency
    maximum_frequency=max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word]=(word_frequencies[word]/maximum_frequency)

    #print(word_frequencies)

    #sentence score
    sentence_scores={}
    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' '))<50:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent]=word_frequencies[word]
                    else:
                        sentence_scores[sent]+=word_frequencies[word]
    #for key,value in sentence_scores.items():
    #    print(key,"Sentence score:",value,end="\n\n")
    #print(sentence_scores)

    #top 7 most frequent sentences
    summary_sentences=heapq.nlargest(10,sentence_scores,key=sentence_scores.get)
    summary=' '.join(summary_sentences)
    response='Summarized Audio:'+summary+'\n\n'+'Transcribed Audio:'+formatted_article_text

    return response