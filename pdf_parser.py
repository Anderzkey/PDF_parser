#!/usr/bin/env python3
"""
PDF Invoice Parser for Russian warehouse invoices
Parses invoice-act.pdf and extracts structured data
"""

import re
import json
from datetime import datetime
import pdfplumber

class InvoiceParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.data = {
            'invoice_info': {},
            'company_info': {},
            'customer_info': {},
            'line_items': [],
            'totals': {},
            'parsed_at': datetime.now().isoformat()
        }
    
    def parse(self):
        """Parse the PDF and extract all data"""
        print(f"Parsing PDF: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            full_text = ""
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"Processing page {page_num}")
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                
                # Try to extract tables
                tables = page.extract_tables()
                if tables:
                    print(f"Found {len(tables)} tables on page {page_num}")
                    self._parse_tables(tables)
        
        # Parse header information
        self._parse_header_info(full_text)
        
        # Parse line items from text
        self._parse_line_items(full_text)
        
        # Parse totals
        self._parse_totals(full_text)
        
        return self.data
    
    def _parse_header_info(self, text):
        """Extract invoice header information"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Invoice number and date
            if 'Детализация к счету №' in line:
                invoice_match = re.search(r'№\s*([\d-]+)\s*от\s*([\d.]+)', line)
                if invoice_match:
                    self.data['invoice_info']['number'] = invoice_match.group(1)
                    self.data['invoice_info']['date'] = invoice_match.group(2)
            
            # Company info (Исполнитель)
            if 'Исполнитель:' in line:
                company_match = re.search(r'Исполнитель:\s*(.+?)\s*,\s*ИНН\s*(\d+)', line)
                if company_match:
                    self.data['company_info']['name'] = company_match.group(1).strip()
                    self.data['company_info']['inn'] = company_match.group(2)
            
            # Customer info (Заказчик)
            if 'Заказчик:' in line:
                customer_match = re.search(r'Заказчик:\s*(.+?)\s*,\s*ИНН\s*(\d+)', line)
                if customer_match:
                    self.data['customer_info']['name'] = customer_match.group(1).strip()
                    self.data['customer_info']['inn'] = customer_match.group(2)
                
                # Extract address and phone if present
                address_match = re.search(r'Адрес:\s*([^,]+(?:,[^,]+)*)\s*,\s*тел\.\s*([\+\d\s\(\)-]+)', line)
                if address_match:
                    self.data['customer_info']['address'] = address_match.group(1).strip()
                    self.data['customer_info']['phone'] = address_match.group(2).strip()
    
    def _parse_line_items(self, text):
        """Extract line items with amounts"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for storage charges (Хранение товаров)
            if 'Хранение товаров от' in line:
                storage_match = re.search(
                    r'Хранение товаров от\s*([\d.]+)\s*до\s*([\d.]+)\s*([\d.,]+)\s*м³\s*([\d.,]+)\s*₽\s*([\d.,]+)\s*₽',
                    line
                )
                if storage_match:
                    item = {
                        'type': 'storage',
                        'description': f"Хранение товаров от {storage_match.group(1)} до {storage_match.group(2)}",
                        'from_date': storage_match.group(1),
                        'to_date': storage_match.group(2),
                        'quantity': float(storage_match.group(3).replace(',', '.')),
                        'unit': 'м³',
                        'price_per_unit': float(storage_match.group(4).replace(',', '.')),
                        'total_amount': float(storage_match.group(5).replace(',', '.'))
                    }
                    self.data['line_items'].append(item)
            
            # Look for reception charges (Приемка товара)
            elif 'Приемка товара на склад' in line:
                reception_match = re.search(
                    r'Приемка товара на склад и размещение\s*(\d+)\s*шт\.\s*([\d.,]+)\s*₽\s*([\d.,]+)\s*₽',
                    line
                )
                if reception_match:
                    item = {
                        'type': 'reception',
                        'description': 'Приемка товара на склад и размещение',
                        'quantity': int(reception_match.group(1)),
                        'unit': 'шт.',
                        'price_per_unit': float(reception_match.group(2).replace(',', '.')),
                        'total_amount': float(reception_match.group(3).replace(',', '.'))
                    }
                    self.data['line_items'].append(item)
            
            # Look for shipment operations (Отгрузка FBO)
            elif 'Отгрузка FBO' in line:
                shipment_match = re.search(r'Отгрузка FBO\s*(\d+)\s*от\s*([\d.]+)', line)
                if shipment_match:
                    item = {
                        'type': 'shipment',
                        'description': f"Отгрузка FBO {shipment_match.group(1)}",
                        'fbo_number': shipment_match.group(1),
                        'date': shipment_match.group(2),
                        'total_amount': 0  # Usually no charge for shipments
                    }
                    self.data['line_items'].append(item)
            
            # Look for reception operations (Приемка with number)
            elif re.match(r'Приемка\s+\d+\s+от', line):
                reception_match = re.search(r'Приемка\s+(\d+)\s+от\s+([\d.]+)', line)
                if reception_match:
                    item = {
                        'type': 'reception_operation',
                        'description': f"Приемка {reception_match.group(1)}",
                        'reception_number': reception_match.group(1),
                        'date': reception_match.group(2),
                        'total_amount': 0  # Usually no charge unless specified
                    }
                    self.data['line_items'].append(item)
    
    def _parse_totals(self, text):
        """Extract total amounts"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Total amount (Итого к оплате)
            if 'Итого к оплате:' in line:
                total_match = re.search(r'Итого к оплате:\s*([\d.,]+)\s*₽', line)
                if total_match:
                    self.data['totals']['total_amount'] = float(total_match.group(1).replace(',', '.'))
            
            # VAT amount (НДС)
            elif 'В том числе НДС:' in line:
                vat_match = re.search(r'В том числе НДС:\s*([\d.,]+)\s*₽', line)
                if vat_match:
                    self.data['totals']['vat_amount'] = float(vat_match.group(1).replace(',', '.'))
            
            # Total items
            elif 'Всего наименований' in line:
                items_match = re.search(r'Всего наименований\s*(\d+)\s*на сумму\s*([\d.,]+)\s*₽', line)
                if items_match:
                    self.data['totals']['total_items'] = int(items_match.group(1))
                    self.data['totals']['total_sum'] = float(items_match.group(2).replace(',', '.'))
    
    def _parse_tables(self, tables):
        """Parse table data if available"""
        for table_num, table in enumerate(tables):
            print(f"Table {table_num + 1} has {len(table)} rows")
            
            # Look for the main services table
            for row_num, row in enumerate(table):
                if row and len(row) >= 5:  # Expected columns: №, Name, Qty, Unit, Price, Sum
                    # Skip header rows
                    if any(header in str(row[0] or '') for header in ['№', 'Наименование']):
                        continue
                    
                    # Try to extract structured data from table rows
                    if row[0] and str(row[0]).isdigit():  # Row number
                        try:
                            item = {
                                'row_number': int(row[0]),
                                'description': str(row[1] or '').strip(),
                                'quantity': self._parse_number(row[2]) if len(row) > 2 else 0,
                                'unit': str(row[3] or '').strip() if len(row) > 3 else '',
                                'price_per_unit': self._parse_number(row[4]) if len(row) > 4 else 0,
                                'total_amount': self._parse_number(row[5]) if len(row) > 5 else 0
                            }
                            
                            # Only add if it has meaningful data
                            if item['description'] and item['total_amount'] > 0:
                                # Add all items with meaningful data, don't skip duplicates
                                # since invoice can have same services for different operations
                                item['type'] = 'table_item'
                                self.data['line_items'].append(item)
                        except (ValueError, IndexError):
                            continue
    
    def _parse_number(self, value):
        """Parse a number from string, handling Russian number format"""
        if not value:
            return 0
        
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Remove currency symbols
        str_value = re.sub(r'[₽\s]', '', str_value)
        
        # Replace comma with dot for decimal separator
        str_value = str_value.replace(',', '.')
        
        # Extract number
        number_match = re.search(r'[\d.]+', str_value)
        if number_match:
            try:
                return float(number_match.group())
            except ValueError:
                return 0
        
        return 0
    
    def save_to_json(self, output_path):
        """Save parsed data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to: {output_path}")
    
    def print_summary(self):
        """Print a summary of parsed data"""
        print("\n=== INVOICE PARSING SUMMARY ===")
        
        # Invoice info
        if self.data['invoice_info']:
            print(f"Invoice Number: {self.data['invoice_info'].get('number', 'N/A')}")
            print(f"Invoice Date: {self.data['invoice_info'].get('date', 'N/A')}")
        
        # Company info
        if self.data['company_info']:
            print(f"Company: {self.data['company_info'].get('name', 'N/A')}")
            print(f"Company INN: {self.data['company_info'].get('inn', 'N/A')}")
        
        # Customer info
        if self.data['customer_info']:
            print(f"Customer: {self.data['customer_info'].get('name', 'N/A')}")
            print(f"Customer INN: {self.data['customer_info'].get('inn', 'N/A')}")
        
        # Line items
        print(f"\nLine Items: {len(self.data['line_items'])}")
        for i, item in enumerate(self.data['line_items'][:5], 1):  # Show first 5
            print(f"  {i}. {item.get('description', 'N/A')[:50]}... - {item.get('total_amount', 0):.2f} ₽")
        
        if len(self.data['line_items']) > 5:
            print(f"  ... and {len(self.data['line_items']) - 5} more items")
        
        # Totals
        if self.data['totals']:
            print(f"\nTotal Amount: {self.data['totals'].get('total_amount', 0):.2f} ₽")
            print(f"VAT Amount: {self.data['totals'].get('vat_amount', 0):.2f} ₽")
            print(f"Total Items: {self.data['totals'].get('total_items', 0)}")

def main():
    """Main function to test PDF parsing"""
    pdf_path = "invoice-act.pdf"
    
    parser = InvoiceParser(pdf_path)
    
    try:
        # Parse the PDF
        data = parser.parse()
        
        # Print summary
        parser.print_summary()
        
        # Save to JSON
        parser.save_to_json("parsed_invoice.json")
        
        print(f"\n✅ PDF parsing completed successfully!")
        print(f"📁 Parsed data saved to: parsed_invoice.json")
        
        return data
        
    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")
        return None

if __name__ == "__main__":
    main()