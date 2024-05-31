from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import requests
import uuid
from pymongo import MongoClient
import re

app = Flask(__name__)
api = Api(app)

MongoDB_Url = 'mongodb+srv://hilaashkenazy:Salasana99@library.odr2f1t.mongodb.net/?retryWrites=true&w=majority&appName=Library'
Books_Url = 'https://localhost:5001/books'

client = MongoClient(MongoDB_Url)
db = client["library"]  # 'library' is the database name
loans = db["loans"]


class Loans(Resource):
    class Loans(Resource):
        def get(self):
            args = request.args
            query = {}

            # Build the MongoDB query based on provided query parameters
            for key, value in args.items():
                # Assume all values are stored as strings; modify if your schema differs
                query[key] = value

            try:
                # Execute the query using MongoDB's find method
                filtered_loans = list(loans.find(query))
            except Exception as e:
                return {'error': 'Database query failed', 'details': str(e)}, 500

            return {'loans': filtered_loans}, 200

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
            return {"error": e}, 422

        if not self.is_valid_date(args['loanDate']):
            return ("error: Invalid date"), 422

        if loans.find_one({'ISBN': args['ISBN']}):
            return {"error": "Book is already on loan"}, 422

        # Check if the member already has 2 or more books on loan
        if loans.count_documents(
                {'memberName': args['memberName']}) >= 2:
            return {"error": "Member has already 2 or more books on loan"}, 422

        query = f"?q=isbn:{args["ISBN"]}"
        try:
            response = request.get(Books_Url + query)
            response.raise_for_status()
            if response.status_code != 200:
                return jsonify({'error': 'Database operation failed'}), 500

            if not response:
                return {"error": "This book is not found in the library"}, 422

            loan_id = str(uuid.uuid4())
            loan = {
                'memberName': args['memberName'],
                'ISBN': args['ISBN'],
                'loanDate': args['loanDate'],
                'title': response.json()['title'],
                'bookID': response.json()['id'],
                'loanID': loan_id
            }
            loans.insert_one(loan)
            return jsonify(loan), 201
        except:
            return {'error': 'unable to add a new loan'}, 404


class Loan(Resource):
    def get(self, loan_id):
        try:
            # Use the find_one method to retrieve the book by its ID from MongoDB
            loan = loans.find_one({'id': loan_id})
            if loan:
                return loan, 200
            else:
                return {'error': 'Loan not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500

    def delete(self, loan_id):
        try:
            # First check if the loan exists
            loan = loans.find_one({'id': loan_id})
            if loan:
                # If the book exists, delete it from the books collection
                loans.delete_one({'id': loan_id})
                return loan_id, 200
            else:
                return {'error': 'Loan not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500

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
api.add_resource(Loan, '/loan/<string:loan_id>')

