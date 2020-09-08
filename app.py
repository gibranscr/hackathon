#!/usr/bin/env python
# coding: utf-8
# In[1]:

import os,sys
from flask import Flask,request
from pymessenger import Bot
from utils import wit_response
from utils import transcribe_audio
from utils import toxicity_data
from utils import handling_and_storage
from utils import ghs_classification
from utils import send_email
import pubchempy as pcp
import yagmail
import requests
import json
import smtplib, ssl
import docx
from socket import gaierror
#from rq import Queue
#from worker import conn

app=Flask(__name__)

PAGE_ACCESS_TOKEN="EAALk0Vc0rZBkBAOc96Wm9cDu2PjsKJrL4KQJTDDkYiUwh4RcAYiCmSZB9dHpXY8kHJ3c0TuZCwVGRCgr0fxiCDzts8Jz5F9FJC4lgCR8S3cTlIFkIasMMMbqxZCyuS8282ZAPGRvmAPTWcpTgXnhYhyaysV3cYgvtr0JYrlSPDZBi2Ama4dllo"
bot=Bot(PAGE_ACCESS_TOKEN)

@app.route('/',methods=['GET'])
def verify():
    if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token")=="hello":
            return "Verification token mismatch",403
        return request.args["hub.challenge"],200
    return "Hello world",200

@app.route('/',methods=['POST'])
#def webhook():
def receive_message():
    data=request.get_json()
    log(data)
    if data['object']=='page':
        messaging_texto=""
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                sender_id=messaging_event['sender']['id']
                recipient_id=messaging_event['recipient']['id']
                    
                if messaging_event.get('message'):
                    
                    if 'text' in messaging_event['message']:
                        messaging_texto=messaging_event['message']['text']
                    else:
                        messaging_texto='no text'
    print(messaging_texto)
    chemical_compound=[]
    intent=None
    Value=""
    chemicals=[]
    chemical_set,intent=wit_response(messaging_texto)
    value=",".join(chemical_set)
    print("wit---",chemical_set,intent)
    if intent=="info_storage_compatibility":
        response="Ok. I will search info about how to store these chemicals:{}".format(str(value))
        #q=Queue(connection=conn)
        #text_audio=q.enqueue(transcribe_audio,value)
        #text_audio=transcribe_audio(value)
        #response=response+'\n\n'+'I found this interesting audio and summarized it:'+str(text_audio)
    elif intent=="confirm_storage_compatibilty":
        response="Ok. I will search info about {} and the chemical compatibilities".format(str(value))
    elif intent=="get_ghs_classification":
        response="Ok. I will search about the GHS Classification for the {}".format(str(value))
    else:
        response="Sorry, I didn't understand!"
    chem={}
    for chemical_compound in chemical_set:
        for compound in pcp.get_compounds(chemical_compound,'name'):
            chem['cid']=compound.cid
            chem['molecular_formula']=compound.molecular_formula
            chem['molecular_weight']=compound.molecular_weight
            chem['isomeric_smiles']=compound.isomeric_smiles
            response_api=""               
            ureceiver_email="contacto@numerica.mx"
            usender_email="anunciosgibsa@gmail.com"
            cid=chem['cid']
            response_result=toxicity_data(chemical_compound,cid)

            if response_result!="":
                response_api=send_email(usender_email,ureceiver_email,chemical_compound,response_result)
            print('chemical_compound',chemical_compound)
            print('chemical_compound',cid)  
            
            if response_api =='Data Sent':
                response_message='We sent you emails with suggestion about toxicity of '+",".join(chemical_set)
            else:
                response_message='We are working on your suggestions, can you try with other chemical'
                    
            print(response_message)
            bot.send_text_message(sender_id,response_message)


    return "ok",200
'''
        def json_extract(obj,key):
            arr=[]
            def extract(obj,arr,key):
                if isinstance(obj,dict):
                    for k,v in obj.items():
                        if isinstance(v,(dict,list)):
                            extract(v,arr,key)
                        elif k==key:
                            arr.append(v)
                elif isinstance(obj,list):
                    for item in obj:
                        extract(item,arr,key)
                return (arr)
            values=extract(obj,arr,key)
            return values
        result=json_extract(data,'text')

        print("result",result)

        nota =request.get_json()
        for event in nota['entry']:
            messaging =event['messaging']
            for message in messaging:
                if message.get('message'):
                    recipient_id=message['sender']['id']


                    if message['message'].get('text'):
                        response_sent_text=message['message']['text']
                        print("text1",response_sent_text)
                       



        


        if data['object']=='page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    sender_id=messaging_event['sender']['id']
                    recipient_id=messaging_event['recipient']['id']
                    
                    if messaging_event.get('message'):
                        if 'text' in messaging_event['message']:
                            messaging_text=messaging_event['message']['text']
                        else:
                            messaging_text='no text'
                        response=None

                        print("text",messaging_text)

                        chemical_compound=[]
                        intent=None
                        Value=""
                        chemicals=[]
                        chemical_set,intent=wit_response(messaging_text)
                        value=",".join(chemical_set)

                        if intent=="info_storage_compatibility":
                            

                            response="Ok. I will search info about how to store these chemicals:{}".format(str(value))
                            #q=Queue(connection=conn)
                            #text_audio=q.enqueue(transcribe_audio,value)
                            #text_audio=transcribe_audio(value)
                            #response=response+'\n\n'+'I found this interesting audio and summarized it:'+str(text_audio)
                        elif intent=="confirm_storage_compatibilty":
                            response="Ok. I will search info about {} and the chemical compatibilities".format(str(value))


                        elif intent=="get_ghs_classification":
                            response="Ok. I will search about the GHS Classification for the {}".format(str(value))
                        else:
                            response="Sorry, I didn't understand!"
                        chem={}
                        for chemical_compound in chemical_set:
                            for compound in pcp.get_compounds(chemical_compound,'name'):
                                chem['cid']=compound.cid
                                chem['molecular_formula']=compound.molecular_formula
                                chem['molecular_weight']=compound.molecular_weight
                                chem['isomeric_smiles']=compound.isomeric_smiles
                            
                            ureceiver_email="contacto@numerica.mx"
                            usender_email="anunciosgibsa@gmail.com"
                            cid=chem['cid']
                            response=toxicity_data(chemical_compound,cid)
                            response_api=send_email(usender_email,ureceiver_email,chemical_compound,response)
                        
                       
                        if response_api =='Data Sent':
                            response_message='We sent you emails with suggestion about toxicity of '+",".join(chemical_set)
                        else:
                            response_message='We could not sent an email with the answer, can you try with other chemical'
                    
                    bot.send_text_message(sender_id,response_message)
                    '''
    #return "ok",200

def log(message):
    print(message)
    sys.stdout.flush()

if __name__=="__main__":
    #app.run(debug=True,port=80)
    app.run()