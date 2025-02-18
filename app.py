from io import BytesIO
from flask import Flask, request, jsonify, send_file, session
import fitz  # PyMuPDF for reading PDFs
from sentence_transformers import SentenceTransformer
import faiss
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from keybert import KeyBERT
from flask_cors import CORS
from model import db, pdf, init_db, recently
import gridfs
from datetime import datetime

app = Flask(__name__)
CORS(app,resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:[root_name]@localhost/drpdf'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.drpdf'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key='!@#$%^&*!@#$%^&*()WERTYUIOghjkhgfxcvbnmjytd'
model = SentenceTransformer("all-MiniLM-L6-v2")
print("model downloaded successfully")

init_db(app)

mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["pdf_storage"]
pdf_collection = mongo_db["pdf_files"]
fs = gridfs.GridFS(mongo_db)



# Function to data --dd-m-yyyy--
def dateextractor(date_str):
    try:
        date_object = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        formatted_date = date_object.strftime("%d-%b-%Y")
        return formatted_date
    except (ValueError, TypeError):
        return date_str

# Function to extract text from the PDF
def extract_text_from_pdf(file_stream):
    """Extract text from a PDF file stream."""
    text = ""
    try:
        # Extract bytes and pass with `filetype='pdf'`
        file_bytes = file_stream.read()
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text


# Function to extract the top 4 keywords from the text
def extract_keywords(text, num_keywords=4):
    """Extract keywords from the text."""
    kw_model = KeyBERT()  # Initialize KeyBERT model
    keywords = kw_model.extract_keywords(text, top_n=num_keywords)
    return [keyword[0] for keyword in keywords]  # Return only the keyword text

@app.route('/upload', methods=['GET','POST'])
def upload():
    try:
        if request.method == 'POST':
            documentname=request.form['documentname']
            documentname=documentname.capitalize()
            f = request.files['file']
            username=request.form["username"]

            print(username)
            pdf_data = f.read()
            f.seek(0)
            pdf_text = extract_text_from_pdf(BytesIO(pdf_data))
            top_keywords = extract_keywords(pdf_text)
            keywords_str = ','.join(top_keywords)
            pdf_id = fs.put(pdf_data, filename=f.filename)
            download_link = f"{str(pdf_id)}"
            upload=pdf(filename=f.filename, user=username,documentname=documentname, keywords=keywords_str , size=len(f.read())/(1024*1024),datalink=download_link, date=datetime.now())
            db.session.add(upload)
            db.session.commit()
            return jsonify({'filename':f.filename,'message':'success'})
        return jsonify({'message':'post function'})
    except Exception as e:
        return jsonify({'message':str(e)})    

@app.route('/recent', methods=['GET','POST'])
def recent():
    username=""
    if(request.method=='POST'):
        username+=request.get_json().get("name")
    print(username)
    recent=db.session.query(recently.datalink).filter(recently.user==username).all()
    datalinks = [r[0] for r in recent]
    pdf_records=db.session.query(pdf.id, pdf.documentname, pdf.date, pdf.datalink).filter(pdf.datalink.in_(datalinks)).all()[::-1]
    records = [{'id': r[0], 'name': r[1], 'dbid': r[3], 'date': dateextractor(r[2])} for r in pdf_records]
    return jsonify(records)
    
@app.route('/download', methods=['GET','POST'])
def download():
    try:
        if request.method=='POST':
            data = request.get_json()
            pdf_id=data.get("pdf_id")
            print(pdf_id)
            file_data = fs.get(ObjectId(pdf_id))
            if(file_data):
                  return send_file(BytesIO(file_data.read()),
                            as_attachment=True,
                            mimetype='application/pdf',
                            download_name=file_data.filename)
            return jsonify({"message":"file not found"}), 404
        return jsonify({"message":"POST function"}), 404
    except Exception as e:
        return jsonify({'message': f'Error downloading file: {str(e)}'}), 404



@app.route('/view', methods=['GET','POST'])
def view():
        if request.method=='POST':
            data = request.get_json()
            pdf_id=data.get("pdf_id")
            print(pdf_id)
            username=data.get("username")
            print(username)
            file_data = fs.get(ObjectId(pdf_id))
            user_entries = recently.query.filter_by(user=username).order_by(recently.created_at).all()
            if len(user_entries) >= 4:
                db.session.delete(user_entries[0])
            recent=recently(user=username, datalink=pdf_id)
            db.session.add(recent)
            db.session.commit()
            if file_data:
                return send_file(
                    BytesIO(file_data.read()),
                    as_attachment=True,
                    mimetype='application/pdf',
                    download_name=file_data.filename
                )
            return jsonify({"message":"file not found"}), 404
        return jsonify({"message":"POST function"}), 404





@app.route('/search', methods=['POST'])
def search():
    try:
        # Get the logged-in user's username
        current_user = request.json.get('name')

        # Fetch user-specific metadata from SQLAlchemy
        user_files = pdf.query.filter_by(user=current_user).all()
        if not user_files:
            return jsonify({'message': 'No files found for the user'}), 404

        # Collect MongoDB ObjectIDs for this user's files
        user_file_links = {file.datalink for file in user_files}
        documents = []
        pdf_records = []

        # Retrieve PDFs from MongoDB matching user's file links
        pdf_files = list(fs.find({'_id': {'$in': [ObjectId(link) for link in user_file_links]}}))
        for file_record in pdf_files:
            pdf_content = file_record.read()
            text_content = extract_text_from_pdf(BytesIO(pdf_content))
            if text_content.strip():
                documents.append(text_content)

        # Ensure documents are available
        if not documents:
            return jsonify({'message': 'No PDF documents found'}), 404

        # Generate embeddings for PDF contents
        embeddings = model.encode(documents, convert_to_tensor=True)

        # Initialize FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.cpu().detach().numpy())

        # Search function
        def search_query(query, top_k=3):
            query_embedding = model.encode([query], convert_to_tensor=True)
            query_embedding_numpy = query_embedding.cpu().detach().numpy()
            distances, indices = index.search(query_embedding_numpy, top_k)
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(user_files):
                    file_metadata = user_files[idx]
                    results.append({
                        'id': file_metadata.id,
                        'name': file_metadata.documentname,
                        'dbid': file_metadata.datalink,
                        'date': dateextractor(file_metadata.date)
                    })
            return results

        # Get user query from JSON
        user_query = request.json.get('query')
        if not user_query:
            return jsonify({'message': 'No query provided'}), 400

        pdf_records = search_query(user_query)
        return jsonify(pdf_records)

    except Exception as e:
        return jsonify({'message': str(e)}), 500



@app.route("/delete", methods=['POST'])
def delete_pdf():
    try:
        if request.method == 'POST':
            data = request.get_json()
            pdfid=data.get("pdfid")
            print(pdfid)
            pdf_record = pdf.query.filter_by(datalink=pdfid).first()
            if pdf_record:
                db.session.delete(pdf_record)
                db.session.commit()
                # Remove from MongoDB
                fs.delete(ObjectId(pdfid))
                return jsonify({"message": "PDF deleted successfully"}), 200
            else:
                return jsonify({"message": "database error PDF not found"})
        return jsonify({"message": "POST PDF not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/allpdfs', methods=['GET', 'POST'])
def allpdfs():
    if(request.method=='POST'):
        data = request.get_json()
        session['username']=data.get("name")
    username=session["username"]
    print(session['username'])
    pdf_records = db.session.query(pdf.id, pdf.documentname, pdf.date, pdf.datalink).filter(pdf.user==username).all()
    records = [{'id': r[0], 'name': r[1], 'dbid': r[3], 'date': dateextractor(r[2])} for r in pdf_records]
    return jsonify(records)

if __name__ == '__main__':
    app.run(debug=False,threaded=False)
    
