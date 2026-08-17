import os
import ibm_boto3
from ibm_botocore.client import Config
from docling.document_converter import DocumentConverter

# --- Configuration from Environment Variables ---
API_KEY = os.getenv('COS_API_KEY', '')
INSTANCE_CRN = os.getenv('COS_CRN', '')
ENDPOINT = os.getenv('COS_ENDPOINT', '')
RAW_BUCKET = 'odpc-raw-pdfs'
PROCESSED_BUCKET = 'odpc-processed-markdown'

print("Starting DPO Co-Pilot Docling Processor...")

# --- Initialize COS Client ---
cos = ibm_boto3.client('s3',
    ibm_api_key_id=API_KEY,
    ibm_service_instance_id=INSTANCE_CRN,
    config=Config(signature_version='oauth'),
    endpoint_url=ENDPOINT
)

def process_documents():
    print(f"Listing objects in {RAW_BUCKET}...")
    objects = cos.list_objects_v2(Bucket=RAW_BUCKET)
    
    converter = DocumentConverter()

    for obj in objects.get('Contents', []):
        file_key = obj['Key']
        if not file_key.lower().endswith('.pdf'):
            continue
            
        print(f"Downloading {file_key}...")
        local_pdf = f"/tmp/{file_key}"
        cos.download_file(RAW_BUCKET, file_key, local_pdf)

        print(f"Processing {file_key} with Docling...")
        # Docling works its magic here
        result = converter.convert(local_pdf)
        markdown_text = result.document.export_to_markdown()

        # Upload the Markdown
        md_key = file_key.replace('.pdf', '.md')
        print(f"Uploading {md_key} to {PROCESSED_BUCKET}...")
        cos.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=md_key,
            Body=markdown_text.encode('utf-8')
        )
        
        # Clean up local file to save memory
        os.remove(local_pdf)

    print("Docling processing complete for all files!")

if __name__ == "__main__":
    process_documents()
