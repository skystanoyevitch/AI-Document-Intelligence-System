import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import base64
import io


load_dotenv()

app = Flask(__name__)
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
            analyze_request=file_content,
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
    
    for document in result.documents:
        receipt = {}
        
        # Extract common receipt fields
        fields = document.fields or {}
        
        # Merchant information
        if "MerchantName" in fields:
            receipt["merchant_name"] = fields["MerchantName"].value
            receipt["merchant_confidence"] = fields["MerchantName"].confidence
        
        if "MerchantAddress" in fields:
            receipt["merchant_address"] = fields["MerchantAddress"].value
        
        if "MerchantPhoneNumber" in fields:
            receipt["merchant_phone"] = fields["MerchantPhoneNumber"].value
        
        # Transaction details
        if "TransactionDate" in fields:
            receipt["transaction_date"] = str(fields["TransactionDate"].value)
        
        if "TransactionTime" in fields:
            receipt["transaction_time"] = str(fields["TransactionTime"].value)
        
        # Financial information
        if "Total" in fields:
            receipt["total"] = fields["Total"].value
            receipt["total_confidence"] = fields["Total"].confidence
        
        if "Subtotal" in fields:
            receipt["subtotal"] = fields["Subtotal"].value
        
        if "TotalTax" in fields:
            receipt["tax"] = fields["TotalTax"].value
        
        # Items
        if "Items" in fields:
            receipt["items"] = []
            for item in fields["Items"].value:
                item_data = {}
                item_fields = item.value
                
                if "Description" in item_fields:
                    item_data["description"] = item_fields["Description"].value
                if "Quantity" in item_fields:
                    item_data["quantity"] = item_fields["Quantity"].value
                if "Price" in item_fields:
                    item_data["price"] = item_fields["Price"].value
                if "TotalPrice" in item_fields:
                    item_data["total_price"] = item_fields["TotalPrice"].value
                
                receipt["items"].append(item_data)
        
        receipts.append(receipt)
    
    return receipts

def format_raw_result(result):
    """Format raw result for debugging purposes"""
    return {
        "model_id": result.model_id,
        "content": result.content[:500] + "..." if len(result.content) > 500 else result.content,
        "document_count": len(result.documents) if result.documents else 0
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)