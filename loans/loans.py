import pymongo
import requests
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import uuid
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

MongoDB_Url = "mongodb://mongo:27017/"

client = pymongo.MongoClient(MongoDB_Url)
db = client["library"]  # 'library' is the database name
loans = db["loans"]
usedIds = db["usedId"]


class Loans(Resource):

    def get(self):
        query = {}

        # Build the MongoDB query based on provided query parameters
        for key, value in request.args.items():
            # Assume all values are stored as strings; modify if your schema differs
            query[key] = value

        try:
            # Execute the query using MongoDB's find method
            filtered_loans = list(loans.find(query, {'_id': 0}))
            return jsonify(filtered_loans)
        except Exception as e:
            return {'error': 'Database query failed', 'details': str(e)}, 500

    def post(self):
        try:

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
                return {"error": "Please enter valid loan details: memberName,ISBN,loanDate"}, 422

            if not is_valid_date(args['loanDate']):
                return {"error": "Invalid date"}, 422

            if loans.find_one({'ISBN': args['ISBN']}):
                return {"error": "Book is already on loan"}, 422

            # Check if the member already has 2 or more books on loan
            if loans.count_documents(
                    {'memberName': args['memberName']}) >= 2:
                return {"error": "Member has already 2 or more books on loan"}, 422

            try:
                isbn = args['ISBN']
                books_url = f'http://books:80/books?ISBN={isbn}'
                response = requests.get(books_url)
                if not response.ok:
                    return {'message': f'Book does not exist in the library'}, 422
            except Exception as e:
                return {'message': f'Error fetching book from library: {str(e)}'}, 500

            try:
                book = response.json()[0]
            except Exception as e:
                return {'message': f'Book does not exist in the library'},422

            while True:
                loan_id = str(uuid.uuid4())
                if usedIds.find_one({'loanID': loan_id}) is None:
                    usedIds.insert_one({'loanID': loan_id})
                    break

            loan = {
                'memberName': args['memberName'],
                'ISBN': args['ISBN'],
                'title': book['title'],
                'bookID': book['id'],
                'loanDate': args['loanDate'],
                'loanID': loan_id
                }
            loans.insert_one(loan)
            return {'loan_id': loan_id}, 201
        except Exception as e:
            return {'error': str(e)}


class Loan(Resource):
    def get(self, loan_id):
        try:
            # Use the find_one method to retrieve the book by its ID from MongoDB
            loan = loans.find_one({'loanID': loan_id}, {'_id': 0})
            if loan:
                return loan, 200
            else:
                return {'error': 'Loan not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500

    def delete(self, loan_id):
        try:
            # First check if the loan exists
            loan = loans.find_one({'loanID': loan_id})
            if loan:
                # If the book exists, delete it from the books collection
                loans.delete_one({'loanID': loan_id})
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
api.add_resource(Loan, '/loans/<string:loan_id>')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)