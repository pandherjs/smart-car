from typing import Union
import smartcar
from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = FastAPI()

cred = credentials.Certificate("fire.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

client = smartcar.AuthClient(
    client_id='42ba14cf-c6fa-4b86-adc9-21d80d981eea',
    client_secret='f2a9a422-bce7-4320-b05d-77a940aff2ec',
    redirect_uri='http://localhost:8000/callback',
    mode='test'
)

############## ROUTES ###################
################ GET URL FOR OAUTH #################
@app.get("/get_url/{user_id}")
def get_url(user_id: str = None):
    if(user_id):
        scopes = ['read_vehicle_info', 'read_odometer', 'read_vin','read_fuel','read_tires','read_engine_oil','read_location']
        options ={
            'state': user_id,
        }
        auth_url = client.get_auth_url(scopes, options)
        data = {
            'user_id': user_id,
        }
        save_user_data(user_id,data)
        return {'status': 200, 'url': auth_url}
    else:
        return {'status': 404, 'message': 'ERROR'}

################ CALLBACK FROM OAUTH #################
@app.get("/callback")
def callback(code: str = None, state: str = None):
    access_object = client.exchange_code(code)
    access_data = {
        'user_id': state,
        'access_token': access_object.access_token,
        'token_type': access_object.token_type,
        'expires_in': access_object.expires_in,
        'expiration': access_object.expiration.isoformat(),  
        'refresh_token': access_object.refresh_token,
        'refresh_expiration': access_object.refresh_expiration.isoformat() 
    }
    save_user_data(state,access_data)
    return {'status': 200}

################ GET ALL VEHICLES #################
@app.get("/all/{user_id}")
def all(user_id: str = None):
    token = get_user_token(user_id)
    vehicles = smartcar.get_vehicles(access_token = token)
    respone = {
        'vehicles': vehicles.vehicles,
        'status' : 200,
    }
    return respone

################ GET INFO FOR ONE VEHICLE #################
@app.get("/get_info/{user_id}/{vehicle_id}")
def all(user_id: str = None, vehicle_id: str = None):
    token = get_user_token(user_id)
    vehicle = smartcar.Vehicle(vehicle_id, token)

    response = {
        'vin': None,
        'oil': None,
        'location': {'lat': None, 'long': None},
        'fuel': {'remaining': None, 'percentage': None, 'range': None},
        'tire': {'front_left': None, 'front_right': None, 'back_left': None, 'back_right': None},
        'information': {'id': None, 'make': None, 'model': None, 'year': None, 'meta': {'request_id': None}}
    }

    # Assuming vehicle is an initialized vehicle object from the Smartcar API
    try:
        attributes = vehicle.attributes()
        if attributes:
            response['information'] = {
                'id': attributes.id,
                'make': attributes.make,
                'model': attributes.model,
                'year': attributes.year,
                'meta': {'request_id': attributes.meta.request_id}
            }
    except Exception as e:
        print(f"Error fetching vehicle attributes: {e}")

    try:
        vin = vehicle.vin()
        response['vin'] = vin.vin
    except Exception:
        pass

    try:
        engine_oil = vehicle.engine_oil()
        response['oil'] = engine_oil.life_remaining
    except Exception:
        pass

    try:
        fuel = vehicle.fuel()
        response['fuel'] = {
            'remaining': fuel.amount_remaining,
            'percentage': fuel.percent_remaining,
            'range': fuel.range,
        }
    except Exception:
        pass

    try:
        location = vehicle.location()
        response['location'] = {'lat': location.latitude, 'long': location.longitude}
    except Exception:
        pass

    try:
        tire_pressure = vehicle.tire_pressure()
        response['tire'] = {
            'front_left': tire_pressure.front_left,
            'front_right': tire_pressure.front_right,
            'back_left': tire_pressure.back_left,
            'back_right': tire_pressure.back_right,
        }
    except Exception:
        pass

    return response


######### FUNCTIONS ################
def save_user_data(user_id,data):
    doc_ref = db.collection('connections').document(user_id)
    doc_ref.set(data)

def get_user_token(user_id):
    query_result = db.collection('connections').where('user_id', '==', user_id).get()
    if query_result:
        document_data = query_result[0].to_dict()
        access_token = document_data.get('access_token')
        return access_token
    else:
        return 404
