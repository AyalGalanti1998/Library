from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import requests
import uuid

app = Flask(__name__)
api = Api(app)

loans = []

Books_Url = 'https://localhost:5001/books'


class Loans(Resource):
    def get(self):
        args = request.args
        filtered_loans = list(loans.values())

        # Filter based on other field=value queries
        for key, value in args.items():
            filtered_loans = [loan for loan in filtered_loans if loan.get(key) == value]

        return {'loans': list(filtered_loans)}, 200

    def post(self):

        # Check the content type of the request to ensure it's JSON
        if request.headers['Content-Type'] != 'application/json':
            return {'error': 'Unsupported media type'}, 415

        # Initialize a request parser to validate and parse input data
        parser = reqparse.RequestParser()
        parser.add_argument('memberName', required=True, help="member name cannot be blank")
        parser.add_argument('ISBN', required=True, help="ISBN cannot be blank")
        parser.add_argument('loanDate', required=True, help="loan date cannot be blank")

        # Parse the input data
        try:
            args = parser.parse_args()
        except Exception as e:
            return {"error: Unprocessable Content"}, 422

        if not self.is_valid_date(args['loanDate']):
            return ("error: Invalid date"), 422

        query = f"?q=isbn:{args["ISBN"]}"
        try:
            response = request.get(Books_Url + query)
        except Exception as e:
            return e,500

        loans.appnd




    def is_valid_date(date_string):
        try:
            year, month, day = date_string.split('-')
            if len(year) == 4 and len(month) == 2 and len(day) == 2:
                year, month, day = int(year), int(month), int(day)
                return 1 <= month <= 12 and 1 <= day <= 31
            return False
        except ValueError:
            return False


api.add_resource(Loans, '/loans')
