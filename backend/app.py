import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import base64
import io

# Only load .env file in development
if os.getenv('WEBSITE_HOSTNAME') is None:  # Not running on Azure
    load_dotenv()

app = Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if not endpoint or not key:
    raise ValueError("Please set the AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables.")


document_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Document Intelligence API"})

@app.route('/analyze-receipt', methods=['POST'])
def analyze_receipt():
    """Analyze receipt from uploaded file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read file content
        file_content = file.read()
        
        # Analyze document using prebuilt receipt model
        poller = document_client.begin_analyze_document(
            "prebuilt-receipt",
            body=file_content,
            content_type="application/octet-stream"
        )
        
        # Get the result
        result = poller.result()
        
        # Extract receipt data
        receipt_data = extract_receipt_fields(result)
        
        return jsonify({
            "success": True,
            "data": receipt_data,
            "raw_result": format_raw_result(result)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_receipt_fields(result):
    """Extract structured data from receipt analysis result"""
    receipts = []

    if not result.documents:
        return receipts
    
    for document in result.documents:
        receipt = {}
        
        # Extract common receipt fields
        fields = document.fields or {}
        
        # Merchant information
        if "MerchantName" in fields:
            receipt["merchant_name"] = fields["MerchantName"].content
            receipt["merchant_confidence"] = fields["MerchantName"].confidence
        
        if "MerchantAddress" in fields:
            receipt["merchant_address"] = fields["MerchantAddress"].content
        
        if "MerchantPhoneNumber" in fields:
            receipt["merchant_phone"] = fields["MerchantPhoneNumber"].content
        
        # Transaction details
        if "TransactionDate" in fields:
            receipt["transaction_date"] = str(fields["TransactionDate"].content)
        
        if "TransactionTime" in fields:
            receipt["transaction_time"] = str(fields["TransactionTime"].content)
        
        # Financial information
        if "Total" in fields:
            receipt["total"] = fields["Total"].content
            receipt["total_confidence"] = fields["Total"].confidence
        
        if "Subtotal" in fields:
            receipt["subtotal"] = fields["Subtotal"].content
        
        if "TotalTax" in fields:
            receipt["tax"] = fields["TotalTax"].content
        
        # Items
        if "Items" in fields and fields["Items"] is not None and fields["Items"].content is not None:
            receipt["items"] = []
            for item in fields["Items"].content:
                item_data = {}

                if item and item.content:
                    item_fields = item.content
                
                if "Description" in item_fields and item_fields["Description"] is not None:
                    item_data["description"] = item_fields["Description"].content
                if "Quantity" in item_fields and item_fields["Quantity"] is not None:
                    item_data["quantity"] = item_fields["Quantity"].content
                if "Price" in item_fields and item_fields["Price"] is not None:
                    item_data["price"] = item_fields["Price"].content
                if "TotalPrice" in item_fields and item_fields["TotalPrice"] is not None:
                    item_data["total_price"] = item_fields["TotalPrice"].content
                
                receipt["items"].append(item_data)
        
        receipts.append(receipt)
    
    return receipts

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

def format_raw_result(result):
    """Format raw result for debugging purposes"""
    return {
        "model_id": result.model_id,
        "content": result.content[:500] + "..." if len(result.content) > 500 else result.content,
        "document_count": len(result.documents) if result.documents else 0
    }

if __name__ == '__main__':
    # For Azure App Service, use the port provided by the environment
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)