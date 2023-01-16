Authors: Erica Chen (ec3589), Chuqi Zhen (cz2416)

PostgreSQL database (user) to grade: cz2416
Project URL: http://35.227.100.166:8111/

URL of the web application:

Description: Digital Recipebook (Cantonese & Fujianese Food) is a database of traditional chinese dishes with information on nutritional data. Entities and relationship sets include recipes that are a type of a cuisine, recipes containing ingredients, authors writing recipes, recipes utilizing cookwares, and ingredients brought from supermarkets. Specific attributes and constraints are shown in the ER diagram below. We will follow the Web Front-end Option to make a web application where you can search by keywords such as macronutrients, measuring units, prep-time, etc. and have recipes (with said attributes) appear.

Data Plan: We will populate the database using recipe information from third party online resources (i.e. Taste Atlas) and primary sources (i.e. parents and grandparents) with information on prep-time, ingredients, nutrients and supplies. We will input the data manually.

Web Front-End Option: Users will be able to search for recipes by authors, type of nutrients, ingredients, and cookware options, etc. The application might ask users for a nutrients category and return as a result a list of recipes. The users can store in the database which recipes they liked and disliked. Also, the application will give recommendations on recipes that the user might like given the user's previously recorded preferences.

Array: We implemented an array data type to the Recipe table to store the links of multiple images of each recipe. The rationale of implementing an array is to store multiple images (for example, images taken from different angles or from different steps of the instructions) in one data structure. We knew we needed more than one image per recipe and storing all images in an array allows for easy access when displaying images at once. Adding the array of images for each recipe improves the user experience of the overall project by adding visuals and balancing the text to visuals ratio.

Text: We added a text data type to the Author table to include a personalized biography about the authors (chefs), which includes detailed information about their prior cooking experience, favorite activities or favorite dishes to make. This improves the user experience of the overall project by creating a sense of relatability between user and authors. The rationale of using the text attribute is that each biography consists of more than one paragraph of natural language text, so using the text attribute is appropriate. The full-text search feature also allows us to search the Author bios that we are interested in by keywords.

Composite: We added a composite that stores various user preferences such as calorie limit, preparation time limit, and whether the dish is spicy or not. With the stored user preferences, the web application can recommend dishes to the users based on these preferences when they log in. This improves the user experience of the overall project by giving users recommendations based on their needs. Also, users are able to edit their preferences anytime in the user profile. The rationale of using the composite type is to better organize distinct factors of recipes, or user’s preferences, into one to be queried and to be used for recipe recommendations. 
