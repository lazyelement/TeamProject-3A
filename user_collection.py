import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template


# Initialize Firebase app
def initialize_firebase():
    # Replace 'path/to/your/firebase-credentials.json' with the actual path to your downloaded JSON key file.
    cred = credentials.Certificate('./keys/williamcollection-a2bba-3986e38ef805.json')
    firebase_admin.initialize_app(cred)


# Function to get the user's collection from Firestore
def get_user_collection(user_id):
    # Get a reference to the "users" collection in Firestore
    users_collection = firestore.client().collection('usercollection')

    # Get the user document with the given user_id
    user_doc = users_collection.document(user_id).get()

    if user_doc.exists:
        collection_ids_dict = user_doc.to_dict()['collections']
        # Convert the dictionary of collection IDs into a list of IDs
        collection_ids_list = list(collection_ids_dict.values())

        # Create a list to store the data for each collection
        collection_data_list = []

        # Loop through the collection IDs and get the data for each collection
        for collection_id in collection_ids_list:
            collection_data = get_collection_data(collection_id)
            if collection_data:
                collection_data_list.append(collection_data)

        if collection_data_list:
            # Categorize the collections based on their category
            categorized_collections = categorize_collections(collection_data_list)

            # Loop through the categorized collections and print the data for each category
            #for category, collections in categorized_collections.items():
                #print(f"Category: {category}")
                #for collection_data in collections:
                  #  print(f"Collection Name: {collection_data['name']}")
                  #  print(f"Image URL: {collection_data['img']}")
                    # Add other fields from the collection_data as needed
                  #  print("--------------")

            return categorized_collections


    else:
        return {}



# Function to get the data for a collection based on collection_id
def get_collection_data(collection_id):
    # Get a reference to the "collections" collection in Firestore
    collections_collection = firestore.client().collection('collectionquestions')

    # Get the collection document with the given collection_id
    collection_doc = collections_collection.document(collection_id).get()

    # If the collection document exists, return the collection data as a dictionary
    if collection_doc.exists:
        collection_data = collection_doc.to_dict()
        return collection_data
    else:
        return None


# Function to categorize the collections based on their category
def categorize_collections(collection_data_list):
    categorized_collections = {}

    for collection_data in collection_data_list:
        category = collection_data.get('category', 'Uncategorized')
        if category not in categorized_collections:
            categorized_collections[category] = []

        categorized_collections[category].append(collection_data)

    return categorized_collections


initialize_firebase()
# Call the get_user_collection function to get the user's collection
categorized_collections = get_user_collection('YG5yTsvG7ceGsXDz4TtkCX3MCvJ3')
for category, collections in categorized_collections.items():
    print(f"Category: {category}")
    for collection_data in collections:
        print(f"Collection Name: {collection_data['name']}")
        print(f"Image URL: {collection_data['img']}")
        print("--------------")