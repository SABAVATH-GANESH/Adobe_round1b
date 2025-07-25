#!/usr/bin/env python3
"""
Web interface for the PDF Intelligence System
Provides a user-friendly web interface for PDF processing
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from src.structure_extractor import StructureExtractor
from src.persona_analyzer import PersonaAnalyzer
from src.utils import setup_logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Setup logging
setup_logging()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and processing"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files selected'}), 400
        
        files = request.files.getlist('files[]')
        processing_mode = request.form.get('mode', 'structure')
        persona = request.form.get('persona', '')
        job_description = request.form.get('job_description', '')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Save uploaded files
        uploaded_files = []
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = Path(app.config['UPLOAD_FOLDER']) / filename
                file.save(filepath)
                uploaded_files.append(filepath)
        
        if not uploaded_files:
            return jsonify({'error': 'No valid PDF files uploaded'}), 400
        
        # Process files
        results = []
        if processing_mode == 'structure':
            # Round 1A: Structure extraction
            extractor = StructureExtractor()
            for pdf_file in uploaded_files:
                start_time = time.time()
                result = extractor.extract_structure(pdf_file)
                elapsed = time.time() - start_time
                
                # Save result
                output_file = Path(app.config['OUTPUT_FOLDER']) / f"{pdf_file.stem}_structure.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                results.append({
                    'filename': pdf_file.name,
                    'processing_time': f"{elapsed:.2f}s",
                    'output_file': output_file.name,
                    'title': result.get('title', 'Unknown'),
                    'sections': len(result.get('outline', []))
                })
        
        elif processing_mode == 'persona':
            # Round 1B: Persona-driven analysis
            if not persona or not job_description:
                return jsonify({'error': 'Persona and job description required for persona analysis'}), 400
            
            analyzer = PersonaAnalyzer()
            config = {
                'persona': persona,
                'job_to_be_done': job_description
            }
            
            start_time = time.time()
            result = analyzer.analyze_documents(uploaded_files, config)
            elapsed = time.time() - start_time
            
            # Save result
            output_file = Path(app.config['OUTPUT_FOLDER']) / "persona_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            results.append({
                'processing_time': f"{elapsed:.2f}s",
                'output_file': output_file.name,
                'documents_processed': len(uploaded_files),
                'relevant_sections': len(result.get('extracted_sections', []))
            })
        
        # Clean up uploaded files
        for file_path in uploaded_files:
            file_path.unlink()
        
        return jsonify({
            'success': True,
            'results': results,
            'processing_mode': processing_mode
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed results"""
    try:
        file_path = Path(app.config['OUTPUT_FOLDER']) / secure_filename(filename)
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def list_results():
    """List all available result files"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        files = []
        for file_path in output_dir.glob('*.json'):
            stat = file_path.stat()
            files.append({
                'name': file_path.name,
                'size': f"{stat.st_size / 1024:.1f} KB",
                'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            })
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)