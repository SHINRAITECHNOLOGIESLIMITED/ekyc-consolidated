import boto3
import json

class TextractProcessor:
    # Define document types
    DOCUMENT_TYPES = {
        'KENYAN_NATIONAL_ID': 'Kenyan National ID',
        'KENYAN_PASSPORT': 'Kenyan Passport',
        'KRA_PIN_CERTIFICATE': 'KRA Pin Certificate',
        'KENYAN_ALIEN_ID': 'Kenyan Alien ID'
    }

    def __init__(self):
        """Initialize the TextractProcessor with AWS clients."""
        self.textract = boto3.client('textract')

    def extract_data(self, textract_response, doc_type):
        """Route to the appropriate extraction method based on document type."""
        if doc_type == 'KENYAN_NATIONAL_ID':
            return self.extract_id_fields(textract_response)
        elif doc_type == 'KENYAN_PASSPORT':
            return self.extract_passport_fields(textract_response)
        elif doc_type == 'KRA_PIN_CERTIFICATE':
            return self.extract_kra_fields(textract_response)
        elif doc_type == 'KENYAN_ALIEN_ID':
            return self.extract_alien_id_fields(textract_response)
        else:
            return {}

    def extract_id_fields(self, textract_response):
        """Extract ID number and full name from Textract response for ID documents."""
        extracted_data = {
            "ID_NUMBER": None,
            "FULL_NAME": None
        }

        # Look for form fields with key-value pairs
        for block in textract_response.get('Blocks', []):
            if block.get('BlockType') == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                # Get the key text
                key_text = self._get_text_from_block_relationships(textract_response, block, 'CHILD')
                key_text = key_text.strip().lower()

                # Check if this key is related to ID number or name
                if any(id_key in key_text for id_key in ['id', 'id no', 'id number', 'identity']):
                    value_text = self._get_value_text(textract_response, block)
                    extracted_data['ID_NUMBER'] = value_text

                elif any(name_key in key_text for name_key in ['name', 'full name', 'names']):
                    value_text = self._get_value_text(textract_response, block)
                    extracted_data['FULL_NAME'] = value_text

        return extracted_data

    def extract_passport_fields(self, textract_response):
        """Extract passport details from Textract response."""
        data = {"PASSPORT_NUMBER": None, "FULL_NAME": None, "NATIONALITY": None}

        # Look for form fields with key-value pairs
        for block in textract_response.get('Blocks', []):
            if block.get('BlockType') == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                # Get the key text
                key_text = self._get_text_from_block_relationships(textract_response, block, 'CHILD')
                key_text = key_text.strip().lower()

                # Check for passport fields
                if any(passport_key in key_text for passport_key in ['passport', 'passport no', 'passport number']):
                    value_text = self._get_value_text(textract_response, block)
                    data['PASSPORT_NUMBER'] = value_text

                elif any(name_key in key_text for name_key in ['name', 'full name', 'names']):
                    value_text = self._get_value_text(textract_response, block)
                    data['FULL_NAME'] = value_text

                elif any(nationality_key in key_text for nationality_key in ['nationality', 'country']):
                    value_text = self._get_value_text(textract_response, block)
                    data['NATIONALITY'] = value_text

        return data

    def extract_kra_fields(self, textract_response):
        """Extract KRA PIN and taxpayer name from Textract response."""
        data = {"KRA_PIN": None, "TAXPAYER_NAME": None}

        # Look for form fields with key-value pairs
        for block in textract_response.get('Blocks', []):
            if block.get('BlockType') == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                # Get the key text
                key_text = self._get_text_from_block_relationships(textract_response, block, 'CHILD')
                key_text = key_text.strip().lower()

                # Check for KRA PIN fields
                if any(pin_key in key_text for pin_key in ['pin', 'kra pin', 'personal identification number']):
                    value_text = self._get_value_text(textract_response, block)
                    data['KRA_PIN'] = value_text

                elif any(name_key in key_text for name_key in ['taxpayer name', 'name', 'taxpayer']):
                    value_text = self._get_value_text(textract_response, block)
                    data['TAXPAYER_NAME'] = value_text

        return data

    def extract_alien_id_fields(self, textract_response):
        """Extract alien ID number and full name from Textract response."""
        data = {"ID_NUMBER": None, "FULL_NAME": None}

        # Look for form fields with key-value pairs
        for block in textract_response.get('Blocks', []):
            if block.get('BlockType') == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                # Get the key text
                key_text = self._get_text_from_block_relationships(textract_response, block, 'CHILD')
                key_text = key_text.strip().lower()

                # Check for alien ID fields
                if any(id_key in key_text for id_key in ['indiv', 'id no', 'id number']):
                    value_text = self._get_value_text(textract_response, block)
                    data['ID_NUMBER'] = value_text

                elif any(name_key in key_text for name_key in ['name', 'full name', 'names']):
                    value_text = self._get_value_text(textract_response, block)
                    data['FULL_NAME'] = value_text

        return data

    def _get_text_from_block_relationships(self, textract_response, block, relationship_type):
        """Helper method to get text from block relationships."""
        text = ""
        for relationship in block.get('Relationships', []):
            if relationship.get('Type') == relationship_type:
                for child_id in relationship.get('Ids', []):
                    for child_block in textract_response.get('Blocks', []):
                        if child_block.get('Id') == child_id and child_block.get('BlockType') == 'WORD':
                            text += child_block.get('Text', '') + " "
        return text.strip()

    def _get_value_text(self, textract_response, key_block):
        """Helper method to get value text from a key block."""
        for relationship in key_block.get('Relationships', []):
            if relationship.get('Type') == 'VALUE':
                for value_id in relationship.get('Ids', []):
                    value_block = next((b for b in textract_response.get('Blocks', []) if b.get('Id') == value_id), None)
                    if value_block:
                        return self._get_text_from_block_relationships(textract_response, value_block, 'CHILD')
        return None

    def process_document(self, bucket, key, doc_type):
        """Process a single document and return extracted data."""
        try:
            # Call Textract to analyze the document
            print(f"Processing {key}...")
            response = self.textract.analyze_document(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}},
                FeatureTypes=["FORMS"]
            )

            # Extract data based on document type
            extracted_info = self.extract_data(response, doc_type)

            return {
                'documentType': doc_type,
                'documentLabel': self.DOCUMENT_TYPES.get(doc_type, 'Unknown Document'),
                'extractedData': extracted_info
            }

        except Exception as e:
            print(f"Error processing document: {str(e)}")
            return None
