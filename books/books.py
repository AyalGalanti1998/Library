import json
from json import dumps
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
import requests
import uuid
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
MongoDB_Url = 'mongodb+srv://hilaashkenazy:Salasana99@library.odr2f1t.mongodb.net/?retryWrites=true&w=majority&appName=Library'

client = MongoClient(MongoDB_Url)
db = client["library"]  # 'library' is the database name
books = db["books"]  # 'books' collection
ratings = db["ratings"]  # 'ratings' collection


class Books(Resource):
    def get(self):
        """
        Retrieves books from the MongoDB collection filtered based on query parameters.
        Supports filtering by various fields.
        """
        # Retrieve query parameters
        args = request.args
        query = {}

        # Convert query parameters directly into a MongoDB query
        for key, value in args.items():
            # Append each query parameter to the MongoDB query dictionary
            query[key] = value

        try:
            # Perform the query using MongoDB's find method
            filtered_books = list(books.find(query))
        except Exception as e:
            return {'error': 'Database query failed', 'details': str(e)}, 500

        # Convert MongoDB documents to a list of dictionaries if needed
        # This step depends on whether your MongoDB driver returns documents as dicts or if you need to convert them
        return {'books': [book for book in filtered_books]}, 200

    def post(self):
        """
        Creates a new book entry based on data provided via a POST request, fetching additional data from external APIs.
        Returns the newly created book details.
        """
        # Check the content type of the request to ensure it's JSON
        if request.headers['Content-Type'] != 'application/json':
            return {'error': 'Unsupported media type'}, 415

        # Initialize a request parser to validate and parse input data
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True, help="Title cannot be blank")
        parser.add_argument('ISBN', required=True, help="ISBN cannot be blank")
        parser.add_argument('genre', required=True, type=str,
                            choices=['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy',
                                     'Other'],
                            help="Genre must be one of 'Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', or 'Other'")

        # Parse the input data
        try:
            args = parser.parse_args()
        except Exception as e:
            return {"error": e}, 422

        # Check if a book with the same ISBN already exists
        if books.find_one({'ISBN': args['ISBN']}):
            return {'error': 'A book with the same ISBN already exists'}, 422

        # Generate a unique ID for the book
        book_id = str(uuid.uuid4())

        # Fetch book data from an external API using the ISBN
        try:
            response = requests.get(f'{BASE_URL}?q=isbn:{args["ISBN"]}')
        except Exception as e:
            return {'error': 'Internal Server Error'}, 500
        book_data = response.json()['items'][0]['volumeInfo'] if response.ok and 'items' in response.json() else {}

        # Handle authors data, defaulting to "missing" if not available
        authors = " and ".join(book_data.get('authors', ['missing']))

        # Fill in the book details
        book_details = {
            'title': args['title'],
            'authors': authors,
            'ISBN': args['ISBN'],
            'publisher': book_data.get('publisher', 'missing'),
            'publishedDate': book_data.get('publishedDate', 'missing'),
            'genre': args['genre'],
            'id': book_id,
        }

        # Store the new book in the MongoDB database
        books.insert_one(book_details)
        ratings.insert_one({'id': book_id, 'values': [], 'average': 0, 'title': args['title']})

        # Return the new book details with 201 Created status
        return {'book_id': book_id}, 201


class Book(Resource):
    def get(self, book_id):
        """
        Retrieves a book by its ID from the MongoDB collection.
        Returns the book details if found, otherwise returns a 404 error.
        """
        try:
            # Use the find_one method to retrieve the book by its ID from MongoDB
            book = books.find_one({'id': book_id})
            if book:
                return book, 200
            else:
                return {'error': 'Book not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500

    def delete(self, book_id):
        """
        Deletes a book by its ID from the MongoDB collection.
        Returns the book ID if successful, otherwise returns a 404 error if the book is not found.
        """
        try:
            # First check if the book exists
            book = books.find_one({'id': book_id})
            if book:
                # If the book exists, delete it from the books collection
                books.delete_one({'id': book_id})
                # Also delete related ratings, if necessary
                ratings.delete_one({'id': book_id})
                return {'message': f'Book with ID {book_id} deleted'}, 200
            else:
                return {'error': 'Book not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500

    class Book(Resource):
        def put(self, book_id):
            """
            Updates the details of a specific book by book_id, validating and storing the provided data.
            """
            # Check the content type of the request to ensure it's JSON
            if request.headers['Content-Type'] != 'application/json':
                return {'error': 'Unsupported media type'}, 415

            data = request.get_json()

            # Verify that the book exists in MongoDB using book_id
            if not books.find_one({'id': book_id}):
                return {'error': 'Book not found'}, 404

            # Initialize a request parser to validate and parse input data
            parser = reqparse.RequestParser()
            parser.add_argument('title', required=True, help="Title cannot be blank")
            parser.add_argument('ISBN', required=True, help="ISBN cannot be blank")
            parser.add_argument('genre', required=True, type=str,
                                choices=['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy',
                                         'Other'],
                                help="Genre must be one of 'Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', or 'Other'")
            parser.add_argument('authors', required=True, help="Authors cannot be blank")
            parser.add_argument('publishedDate', required=True, help="Published Date cannot be blank")
            parser.add_argument('publisher', required=True, help="Publisher cannot be blank")

            try:
                # Parse the request arguments based on the defined rules
                args = parser.parse_args()
            except Exception as e:
                return {"error": e}, 422

            # Update the book details in MongoDB
            update_fields = {
                'title': args['title'],
                'authors': args['authors'],
                'ISBN': args['ISBN'],
                'publisher': args['publisher'],
                'publishedDate': args['publishedDate'],
                'genre': args['genre'],
            }

            try:
                # Update the document using MongoDB's update_one method
                books.update_one({'id': book_id}, {'$set': update_fields})
                return {'message': 'Book updated successfully', 'id': book_id}, 200
            except Exception as e:
                return {'error': 'Database update failed', 'details': str(e)}, 500


class Ratings(Resource):
    def get(self):
        """
        A Resource class to fetch ratings based on filter criteria provided through query parameters.
        """
        args = request.args
        query = {}

        # Build the MongoDB query based on provided query parameters
        for key, value in args.items():
            # Assume all values are stored as strings; modify if your schema differs
            query[key] = value

        try:
            # Execute the query using MongoDB's find method
            filtered_ratings = list(ratings.find(query))
        except Exception as e:
            return {'error': 'Database query failed', 'details': str(e)}, 500

        return {'ratings': filtered_ratings}, 200


class Rating(Resource):
    def get(self, rate_id):
        """
        A Resource class to fetch ratings for a specific book using its rate_id.
        """
        try:
            # Use the find_one method to retrieve the rating by its ID from MongoDB
            rating = ratings.find_one({'id': rate_id})
            if rating:
                return rating, 200
            else:
                return {'error': 'Rating not found'}, 404
        except Exception as e:
            return {'error': 'Database operation failed', 'details': str(e)}, 500


class RateValues(Resource):
    def post(self, rate_id):
        """
        A Resource class to handle the POST requests for adding new ratings to books.
        """
        # Verify if the specified rate_id exists in the MongoDB ratings collection
        rating = ratings.find_one({'id': rate_id})
        if not rating:
            return {'error': 'Rating not found'}, 404

        data = request.get_json()
        if request.headers['Content-Type'] != 'application/json':
            return {'error': 'Unsupported media type'}, 415  # Return error if content type is not JSON

        # Validate that the data includes a 'value' key and that the value is between 1 and 5
        if not data or 'value' not in data or not (1 <= data['value'] <= 5):
            return {"error": "Unprocessable Content"}, 422  # Return error if the value is not valid

        try:
            # Append the new value to the list of values for this book's ratings
            new_values = rating['values'] + [data['value']]
            # Calculate the new average rating after adding the new value
            new_average = sum(new_values) / len(new_values)
            # Update the values and average in the MongoDB document
            ratings.update_one({'id': rate_id}, {'$set': {'values': new_values, 'average': new_average}})
            return {'new_average': new_average}, 201
        except Exception as e:
            return {'error': 'Database update failed', 'details': str(e)}, 500


class Top(Resource):
    """
        A Resource class to fetch the top-rated books from a collection based on at least 3 ratings.
        """

    def get(self):
        # Filter books that have at least 3 ratings.
        pipeline = [
            {"$match": {"values": {"$size": 3}}},
            {"$sort": {"average": -1}},
            {"$limit": 3}  # Limits the result to top 3
        ]
        top_ratings = list(ratings.aggregate(pipeline))

        # Additional logic to include ties at the 3rd place if necessary
        if len(top_ratings) == 3:
            third_average = top_ratings[-1]['average']
            tie_ratings = list(ratings.find({"average": third_average}))
            if len(tie_ratings) > 1:
                top_ratings.extend([rating for rating in tie_ratings if rating not in top_ratings])

        return jsonify(json.loads(dumps(top_ratings)))


api.add_resource(Books, '/books')
api.add_resource(Book, '/books/<string:book_id>')
api.add_resource(Ratings, '/ratings')
api.add_resource(Rating, '/ratings/<string:rate_id>')
api.add_resource(RateValues, '/ratings/<string:rate_id>/values')
api.add_resource(Top, '/top')

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5001, debug=True)
