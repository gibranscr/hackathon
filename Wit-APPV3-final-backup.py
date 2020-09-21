#!/usr/bin/env python
# coding: utf-8

# In[6]:


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
import pubchempy as pcp
import smtplib,ssl
import requests
import json
import pandas as pd
import time
import yagmail        
from wit import Wit


chemicals=[]
ureceiver='numerica.electronics@gmail.com'
usender="anunciosgibsa@gmail.com"
access_token_wit='FE5AVTCKI4WL7X2S4RCZPS4L7D53S5QP'
#question='Can I combine the benzene and methanol?'
question=input('Please ask a question about the chemical compound that you want to know about:')
def wit_request(question,access_token_wit):
    
    client = Wit(access_token=access_token_wit)
    resp=client.message(msg=question)

    data_extraction=json.dumps(resp)
    data=json.loads(data_extraction)


    def depth(data):
        if "entities" in data:
            return 1 +  max([0] + list(map(depth, data['entities'])))      
        else:
            return 1
    levels_with_entities=depth(data)


    #print(json.dumps(data,indent=2,sort_keys=True))
    
    def json_extract(obj,key):
        arr=[]
        def extract(obj,arr,key):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if isinstance(v,(dict,list)):
                        extract(v,arr,key)
                    elif v==key:
                        if obj not in arr:
                            arr.append(obj)
            elif isinstance(obj,list):
                for item in obj:
                    extract(item,arr,key)
            return (arr)
        values=extract(obj,arr,key)
        return values
    #get intents
    intent=resp['intents'][0]['name']
    #extract chemicals that wit.ai found
    result_confirm=json_extract(data,'chemical_substance')
    chemicals=[]
    number_chemicals=len(result_confirm)
    for q in range(number_chemicals):
        chemicals.append(result_confirm[q]['value'])   
    
    #print(json.dumps(result_confirm,indent=2,sort_keys=True))
    #print('result confirm:',chemicals,intent)#result_confirm)
    
    return (chemicals,intent)


def summarizing_video(chemical_compound):
    confirmation_video=""
    summary=''
    formatted_article_text=''
    max_elements=1
    #results=YoutubeSearch('Benzene',max_results=5).to_json()
    results=YoutubeSearch(chemical_compound,max_results=max_elements).to_dict()
    #print(results)
   
    def validate_reply(confirmation_video):
        
        confirmation_verified=''
        if confirmation_video=='YES' or confirmation_video=='NO':
            confirmation_verified=confirmation_video
            return confirmation_verified
        else:
            print('Please confirm that you want me to transcribe it?')
            confirmation_video=input('(yes/no):').upper()
            return validate_reply(confirmation_video)
    
    for i in range(max_elements):
       
        url="https://www.youtube.com/watch?v="+results[i]['id']
        title_video=results[i]['title']
        duration=results[i]['duration']
        views=results[i]['views']
        print('I found this video, do you want me to transcribe it?\n')
        print('****************')
        print("Title: ",title_video)
        print('Duration',duration)
        print("Url",url)
        print("Views",views)
        print("***************")
        confirmation_video=input('Transcribing video? (yes/no):').upper()
        confirmation_verified=validate_reply(confirmation_video)
        print('out',confirmation_verified)
        if confirmation_verified=='YES':
            print('in',confirmation_verified)
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

            #top 7 most frequent sentences
            summary_sentences=heapq.nlargest(10,sentence_scores,key=sentence_scores.get)
            summary=' '.join(summary_sentences)
        
    return (summary,formatted_article_text)


#find the email
def send_email(ureceiver,usender,body,result_content,email_title):
    if not result_content:
        result_content='No records found, please search with synonyms.'
        
    receiver=ureceiver
    body="Hello, Buddy!"
    body+="This is an email with the information requested on the chat. Hope you find it hepful"
    yag=yagmail.SMTP("anunciosgibsa@gmail.com","VentaProduct51g")
    email_sent=yag.send(to=receiver,
            subject=email_title,
            contents=result_content)
    if not email_sent:
        email_confirmation='Email Sent'
    else:
        email_confirmation='Email Not Sent'
    return email_confirmation

#find info safe storage
def info_safe_storage():
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
    result_validate_safe=json_extract(result_safe,'Not Classified')
    result_validate_storage=json_extract(result_storage,'Not Classified')

    response_title='Handling and Storage Summary:\n'
    if len(result_safe[0])==0 and len(result_storage[0])==0:
        if result_validate_storage[0]['validate']=='Not Classified' and result_validate_safe[0]['validate']=='Not Classified':
            response_api="There are are not records of hazard classification so that it may not be dangerous, please look for other professional resources"
            response=response_title+response_api
    else:
        print('Continue')

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
    return response

#find toxicity documentation
def toxicity(chemical_compound,cid):
    
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
    result_validate=json_extract(result,'Not Classified')
    #print(json.dumps(result_validate,indent=2,sort_keys=True))

    
    response_title='Toxicity Summary:\n'
    if len(result[0])==0:
        if len(result_validate)>=1:
            response_api="There are are not records of hazard classification so that it may not be dangerous, please look for other professional resources"
            result_toxicity=response_title+response_api
    else:
        toxicity={}
        for key,value in result[0].items():
            if value not in toxicity.values():
                toxicity[key]=value

        result_toxicity=toxicity['Information'][0]['Value']['StringWithMarkup'][0]['String']
    return result_toxicity

#find handling & storage characteristics
def handling_store(chemical_compound,cid):
    
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
    result=json_extract(textt,'Handling and Storage')
    result_validate=json_extract(result,'Not Classified')

    #print('handling55:',result)
    #print(json.dumps(result,indent=2,sort_keys=True))
    result_handling_storage=''
    response_title='Handling and Storage:\n\n'
    #si no hay devolucion de datos
    if len(result[0])==0:
        if result_validate[0]['validate']=='Not Classified':
            response_api="There are are not records of hazard classification so that it may not be dangerous, please look for other professional resources"
            result_handling_storage=response_title+response_api
            #print('No results:',result_handling_storage)
    else:
        handling_storage={}
        result_handling_storage=''
        for key,value in result[0].items():
            if value not in handling_storage.values():
                handling_storage[key]=value

        result_handling_storage=handling_storage['Section'][0]['Information'][0]['Value']['StringWithMarkup'][0]['String']
    return result_handling_storage

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
    result=json_extract(textt,'GHS Classification')
    result_validate=json_extract(result,'Not Classified')
    #print(json.dumps(result_validate,indent=2,sort_keys=True))
    #print(json.dumps(result,indent=2,sort_keys=True))
    
    response_title="GHS Classification:\n"
    
    if len(result[0])==0:
        if result_validate[0]['validate']=='Not Classified':
            response_api="There are are not records of hazard classification so that it may not be dangerous, please look for other professional resources"
            response_ghs_classification=response_title+response_api
    else:
        results=json_extract(textt,'Pictogram(s)')
        ghs_classification={}
        for key,value in results[0].items():
            if value not in ghs_classification.values():
                ghs_classification[key]=value

        #print(json.dumps(ghs_classification,indent=2,sort_keys=True))
        response_api=""
        response=''
        number_classified=len(ghs_classification['Value']['StringWithMarkup'][0]['Markup'])
        
        #print("number:",number_classified)
        ghs_class=ghs_classification['Value']['StringWithMarkup'][0]['Markup']
              
        for ghs in range(number_classified):
           #print(ghs_class[ghs]['Extra'])
            response=ghs_class[ghs]['Extra']+" "
            response_api+=response
        response_ghs_classification=response_title+response_api
        #print(response_ghs_classification)
    return response_ghs_classification


def content_sorted(chemicals,title_total_content,intent_chemical_request):
    chemical={}
    content=''
    response=''
    cid=''
    for chemical_compound in chemicals:
        for compound in pcp.get_compounds(chemical_compound,'name'):
            chemical['cid']=compound.cid
            cid=compound.cid

        #print("--->",chemical_compound,chemical['cid'])
        if intent_chemical_request=="confirm_storage_compatibility":
            
            title="Chemical Compatibility Info: "+chemical_compound.upper()+"\n\n"
            content_csc=handling_store(chemical_compound,cid)
            
            response=title+content_csc
            
        elif intent_chemical_request=="get_ghs_classification":
            title="GHS Info: "
            response_ghs=ghs_classification(chemical_compound,cid)
            content_title=title+chemical_compound.upper()+"\n\n"
            content_ghs= content_title+"\n\n"+response_ghs
            
            toxicity_title='Toxicity Summary: '+chemical_compound.upper()+"\n\n"
            result_content_toxicity=toxicity(chemical_compound,chemical['cid'])
            content_toxicity=toxicity_title+result_content_toxicity
 
            response=content_ghs+content_toxicity
            
        elif intent_chemical_request=="info_storage_compatibility":
            
            title_si="Storage Information: "+chemical_compound.upper()+"\n\n"
            result_content_ghs=ghs_classification(chemical_compound,cid)
            total_content_si=title_si+result_content_ghs
            
            title_sc="Storage Compatibility Info: "+chemical_compound.upper()+"\n\n"
            content_csc=handling_store(chemical_compound,cid)
            total_content_csc=title_sc+content_csc
            
            response=total_content_si+total_content_csc

        #content_chemical=chemical_compound.upper()+"\n"
        #content= content_chemical+response+"\n\n"+content
        content= response+"\n\n"+content
    full_content=title_total_content+content+"\n\n"
    print('ful text:',full_content)
    return full_content

#-----Wit.Ai request to identify intents and more tasks----
def validate_reply(confirmation_video):
    confirmation_verified=''
    if confirmation_video=='YES' or confirmation_video=='NO':
        confirmation_verified=confirmation_video
        return confirmation_verified
    else:
        confirmation_video=input('Please confirm that you want me to transcribe it? (yes/no):').upper()
        return validate_reply(confirmation_video)
    
chemical={}
chemicals=[]
wit_results=wit_request(question,access_token_wit)
print('Wit results New:',wit_results)
#request trutful information from PubChemAPI
for chem in wit_results[0]:
    chemicals.append(chem)
    chemical_compound=chem
    
    intent=wit_results[1]
    for compound in pcp.get_compounds(chemicals,'name'):
        chemical['cid']=compound.cid
        cid=compound.cid
    body='PubChem Library API'
    #intent='get_ghs_classification' 
    if intent=="confirm_storage_compatibility":
        #result_content=content_sorted("Globally Harmonized System Hazard Classification",handling_store(chemical_compound,chemical['cid']))  
        
        email_title="Compatibility - Globally Harmonized System Hazard Classification: "+chemical_compound.upper()
        result_content=content_sorted(chemicals,email_title,intent)
        email_confirmation=send_email(ureceiver,usender,body,result_content,email_title)    
        print("Sending confirmation;",email_confirmation)
    elif intent=="get_ghs_classification":
        email_title="Summarized Documentation: "+chemical_compound.upper()
        full_content=content_sorted(chemicals,email_title,intent)
        email_confirmation=send_email(ureceiver,usender,body,full_content,email_title)

    else:#info_storage_classification
        
        email_title="Storage Information (Globally Harmonized System Hazard Classification): "+chemical_compound.upper()
        result_content=content_sorted(chemicals,email_title,intent)
        email_confirmation=send_email(ureceiver,usender,body,result_content,email_title)
    
    confirmation_video=''
    answer=input('Would you like me to look for a video about '+chemical_compound+' on youtube video to transcribe into text and make a summary of the video? (yes/no) ').upper()#+str(chem)).upper()
    #Extract full text and summa
    
    if answer=='YES' or answer=='NO':
        confirmation_video=answer
    else:
        confirmation_video=validate_reply(confirmation_video)
    
    if answer=='YES' or confirmation_video=='YES':
        #print(chem,"---->")
        summary_text,full_video_text=summarizing_video(chemical_compound)
        print(full_video_text,"----",summary_text)
        email_title="Video Summary: "+chemical_compound
        full_documentation=summary_text+"\n\n"+"Full Text: "+full_video_text
       
        if full_video_text:
            full_text=send_email(ureceiver,usender,body,full_documentation,email_title)
            print(full_text)
            Email_confirmed="Email Sent"
            print("You will receive an email soon with the full text and summary")
        
        else:
            print("There woon't be any email sent")
    else:
        pass

        
if email_confirmation == "Email Sent":
    print('Email Sent: You will receive your summarized info on your registered email soon.')
else:
    print('Not Email Sent: There was not enough information to send you.')     

    
#print(email_confirmation)
#print(full_content)

print('Finished...')


# In[ ]:





# In[ ]:





# In[ ]:




