import json
import re
from typing import Dict, List, Any
from docx import Document
import pdfplumber
import os
def read_docx_file(file_path: str) -> str:
    """
    Read content from a .docx file
    """
    try:
        doc = Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)
        return '\n'.join(content)
    except Exception as e:
        print(f"Error reading .docx file: {e}")
        return ""
import pdfplumber

def read_pdf_file(file_path: str) -> str:
    """
    Extract text from a PDF file
    """
    try:
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_content.append(page.extract_text() or "")
        return "\n".join(text_content)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def parse_wcart_manual_to_json(content: str) -> Dict[str, Any]:
    data = {}
    current_section = None
    lines = content.split('\n')
    
    # Regex to detect headings (e.g., "SECTION 1", "INTRODUCTION")
    # This assumes headings are in all caps and not excessively long.
    heading_pattern = re.compile(r'^[A-Z0-9\s\-:]+$')

    for line in lines:
        text = line.strip()
        if not text:
            continue
        
        # Heuristic for detecting a heading
        if heading_pattern.match(text) and len(text) < 100:
            current_section = text
            data[current_section] = {"content": "", "subsections": {}}
        else:
            if current_section:
                data[current_section]["content"] += text + "\n"
            # Optional: handle content that appears before the first heading
            else:
                if "Introduction" not in data:
                    data["Introduction"] = {"content": "", "subsections": {}}
                data["Introduction"]["content"] += text + "\n"
    
    return data


def convert_to_html(text: str) -> str:
    """
    Convert text formatting to HTML with proper list handling
    """
    if not text:
        return ""
    
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    html_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        lines = paragraph.split('\n')
        html_lines = []
        current_list = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for bullet points
            if line.startswith('- ') or line.startswith('• ') or re.match(r'^\d+\.\s+', line):
                if not in_list:
                    in_list = True
                    current_list = []
                
                # Clean list item
                if line.startswith('- '):
                    item = line[2:].strip()
                elif line.startswith('• '):
                    item = line[2:].strip()
                else:
                    item = re.sub(r'^\d+\.\s+', '', line).strip()
                
                # Convert formatting within list item
                item_html = convert_formatting(item)
                current_list.append(f"<li>{item_html}</li>")
                
            else:
                # End current list
                if in_list and current_list:
                    list_tag = "ol" if re.match(r'^\d+\.', lines[0]) else "ul"
                    html_lines.append(f"<{list_tag}>{''.join(current_list)}</{list_tag}>")
                    current_list = []
                    in_list = False
                
                # Convert regular line
                html_lines.append(convert_formatting(line))
        
        # Add any remaining list
        if in_list and current_list:
            list_tag = "ol" if re.match(r'^\d+\.', lines[0]) else "ul"
            html_lines.append(f"<{list_tag}>{''.join(current_list)}</{list_tag}>")
        
        # Join lines with breaks
        if html_lines:
            html_paragraphs.append('<br>'.join(html_lines))
    
    return '<br><br>'.join(html_paragraphs)

def convert_formatting(text: str) -> str:
    """
    Convert inline formatting to HTML
    """
    # Bold text **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Italic text *text*
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Underlined text
    text = re.sub(r'_(.*?)_', r'<u>\1</u>', text)
    
    # Code/monospace `text`
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Arrows and special characters
    text = text.replace('→', '&rarr;')
    text = text.replace('←', '&larr;')
    text = text.replace('↑', '&uarr;')
    text = text.replace('↓', '&darr;')
    
    return text

def main():
    file_path = 'Copy of WCART USER MANUAL.pdf'
    content = ""
    
    try:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".docx":
            content = read_docx_file(file_path)
        elif ext == ".pdf":
            content = read_pdf_file(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return
        
        if not content:
            print(f"No content could be extracted from '{file_path}'.")
            return
                
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        print("Please make sure the file exists in the current directory.")
        return
    
    # Parse the content to JSON
    wcart_json = parse_wcart_manual_to_json(content)
    
    # Save to JSON file
    output_file = 'wcart_manual1.json'
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(wcart_json, json_file, indent=2, ensure_ascii=False)
    
    print("✅ WCART manual converted to JSON successfully!")
    print(f"📁 Output file: {output_file}")
    print(f"📊 Sections processed: {len(wcart_json)}")
    
    # Display summary
    total_subsections = 0
    for section, data in wcart_json.items():
        subsections_count = len(data.get("subsections", {}))
        total_subsections += subsections_count
        content_length = len(data.get("content", ""))
        print(f"• {section}: {subsections_count} subsections, {content_length} chars")
    
    print(f"📈 Total subsections: {total_subsections}")

if __name__ == "__main__":
    main()