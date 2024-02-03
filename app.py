from flask import Flask, request, redirect
import smartcar
import firebase_admin
from firebase_admin import credentials, firestore
import shortuuid
from datetime import datetime
import uuid

app = Flask(__name__)

cred = credentials.Certificate("fire.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

client = smartcar.AuthClient(
    client_id='42ba14cf-c6fa-4b86-adc9-21d80d981eea',
    client_secret='f2a9a422-bce7-4320-b05d-77a940aff2ec',
    redirect_uri='http://localhost:5000/callback',
    mode='test'
)
scopes = ['read_vehicle_info', 'read_odometer']

@app.route("/")
def hello_world():
    auth_url = client.get_auth_url(scopes)
    user_id= '123456789'
    query = db.collection('connections').where('user_id', '==', user_id).get()
    if query:
        document_data = query[0].to_dict()
        access_token = document_data.get('access_token')        
        vehicles = smartcar.get_vehicles(access_token)
        print(vehicles)
        return 'OK'

    else:
        print("No document found for the given user_id.")
        return f"<a href='{auth_url}'>Connect</a>"

@app.route("/callback")
def callback():
    code = request.args.get('code')
    access_object = client.exchange_code(code)
    print(access_object)
    save_access_token_to_firestore('123456789', access_object)
    return redirect("/")

def get_fresh_access(code):
    new_access = client.exchange_refresh_token(code['refresh_token'])
    return new_access

def save_access_token_to_firestore(user_id, access_object):
    access_data = {
        'user_id': user_id,
        'access_token': access_object.access_token,
        'token_type': access_object.token_type,
        'expires_in': access_object.expires_in,
        'expiration': access_object.expiration.isoformat(),  
        'refresh_token': access_object.refresh_token,
        'refresh_expiration': access_object.refresh_expiration.isoformat() 
    }

    doc_ref = db.collection('connections').document(user_id)
    doc_ref.set(access_data)


    # def generate_id(length):
    # s = uuid.uuid4().hex
    # s.random(length=length)