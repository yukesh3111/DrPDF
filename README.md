# AI-Powered PDF Search System

## Overview
This AI-powered PDF search system allows users to upload, search, view, and download PDFs efficiently. The system utilizes **FAISS for vector search**, **Sentence Transformers for semantic search**, and **MongoDB with GridFS** for efficient storage and retrieval. It is built using **Flask** and supports keyword extraction using **KeyBERT**.

## Features
- Upload and store PDFs securely.
- Extract text and keywords automatically from PDFs.
- Perform AI-powered search using **FAISS** and **Sentence Transformers**.
- View and download PDFs directly from the interface.
- Keep track of recently viewed documents.
- User-based document management with SQLAlchemy and MongoDB.

## Installation
### Prerequisites
Ensure you have the following installed:
- **Python 3.7+**
- **MongoDB** (running locally)
- **MySQL** (configured for user authentication)
- Required Python dependencies

### Install Dependencies
```sh
pip install -r requirements.txt```

## Configuration
Update `app.config` in `app.py` with your database credentials:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:yourpassword@localhost/yourdbname'
```
Ensure MongoDB is running on **localhost:27017**.

## Usage
### Run the Application
```sh
python app.py
```
### API Endpoints
| Method | Endpoint       | Description |
|--------|---------------|-------------|
| POST   | `/upload`     | Upload a PDF file |
| POST   | `/search`     | Search within uploaded PDFs |
| POST   | `/download`   | Download a PDF by ID |
| POST   | `/view`       | View a PDF online |
| POST   | `/delete`     | Delete a PDF by ID |
| POST   | `/recent`     | Retrieve recently viewed PDFs |
| POST   | `/allpdfs`    | List all PDFs uploaded by a user |

## File Structure
```
/
├── app.py                  # Main Flask application
├── model.py                # Database models
├── requirements.txt        # Dependencies
├── README.md               # Documentation
```

## Example Request
### Upload a PDF
```sh
curl -X POST -F "file=@sample.pdf" -F "username=testuser" -F "documentname=Sample" http://localhost:5000/upload
```

### Search a Query
```sh
curl -X POST -H "Content-Type: application/json" -d '{"name":"testuser", "query":"fastest bike"}' http://localhost:5000/search
```

## Contributing
Pull requests are welcome! Fork the repository and submit a PR.

## License
This project is licensed under the **MIT License**.

## Author
Developed by **YUKESH P**

