from flask_restful import Resource, reqparse
from model.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3
from filtros import normalize_path_params, consulta_sem_cidade, consulta_com_cidade

path_paramns = reqparse.RequestParser()
path_paramns.add_argument('cidade', type=str)
path_paramns.add_argument('estrelas_min', type=float)
path_paramns.add_argument('estrelas_max', type=float)
path_paramns.add_argument('diaria_min', type=float)
path_paramns.add_argument('diaria_max', type=float)
path_paramns.add_argument('limit', type=float)
path_paramns.add_argument('offset', type=float)

#------------------------------------------------------------------------------#
class Hoteis(Resource):
    def get(self):
        connection = sqlite3.connect('banco.db')
        cursor = connection.cursor()

        dados = path_paramns.parse_args()
        dados_validos = {chave: dados[chave] for chave in dados if dados[chave] is not None}
        parametros =  normalize_path_params(**dados_validos)

        if not parametros.get('cidade'):
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_sem_cidade, tupla)
                        
        else:   
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_com_cidade, tupla)  

        hoteis = []    
        for linha in resultado:
            hoteis.append({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'diaria': linha[3],
                'cidade': linha[4]
            })

        return {'hoteis': hoteis}


#------------------------------------------------------------------------------#
class Hotel(Resource):
    atributos = reqparse.RequestParser()
    atributos.add_argument('nome', type=str, required=True, help="The field 'nome' cannot be left blank.")
    atributos.add_argument('estrelas', type=float, required=True, help="The field 'estrelas' cannot be left blank.")
    atributos.add_argument('diaria', type=float, required=True, help="The field 'diaria' cannot be left blank.")
    atributos.add_argument('cidade', type=str, required=True, help="The field 'cidade' cannot be left blank.")

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': f'Hotel with ID {hotel_id} not found.'}, 404

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {"message": "Hotel id '{}' already exists.".format(hotel_id)}, 400
        dados = Hotel.atributos.parse_args()
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'An internal error ocurred trying to save hotel.'}, 500  # Internal Server Error
        return hotel.json(), 201

    @jwt_required()
    def put(self, hotel_id):
        dados = Hotel.atributos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)

        if hotel_encontrado:
            try:
                hotel_encontrado.update_hotel(**dados)
                hotel_encontrado.save_hotel()
                return hotel_encontrado.json(), 200
            except Exception as e:
                return {'message': f'An error occurred while updating hotel: {str(e)}'}, 500
        else:
            try:
                hotel = HotelModel(hotel_id, **dados)
                hotel.save_hotel()
                return hotel.json(), 201
            except Exception as e:
                return {'message': f'An error occurred while creating hotel: {str(e)}'}, 500

    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'An error ocurred trying to delete hotel.'}, 500
            return {'message': 'Hotel deleted.'}
        return {'message': 'Hotel not found.'}, 404