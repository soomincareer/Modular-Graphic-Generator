#!/usr/bin/env python3
"""
Module Grid Generator Web Application
Flask 기반 웹 인터페이스
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import numpy as np

from module_grid_generator import ModuleGridGenerator, process_folder

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image_path):
    """이미지를 base64로 인코딩"""
    with Image.open(image_path) as img:
        # 썸네일 크기로 축소
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-modules', methods=['POST'])
def analyze_modules():
    """모듈 폴더 분석 - 밝기 순으로 정렬된 정보 반환"""
    try:
        # 모듈 파일 업로드 처리
        module_files = request.files.getlist('module_files')

        if not module_files:
            return jsonify({'error': '모듈 파일을 선택해주세요.'}), 400

        # 임시 모듈 폴더 생성
        module_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'modules')
        os.makedirs(module_folder, exist_ok=True)

        # 파일 저장
        saved_files = []
        for file in module_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(module_folder, filename)
                file.save(filepath)
                saved_files.append(filepath)

        if not saved_files:
            return jsonify({'error': '유효한 이미지 파일이 없습니다.'}), 400

        # 모듈 분석
        modules_info = []
        module_brightness = []

        for filepath in saved_files:
            img = Image.open(filepath).convert('L')
            brightness = np.array(img).mean()

            modules_info.append({
                'filename': os.path.basename(filepath),
                'brightness': float(brightness),
                'image': image_to_base64(filepath)
            })
            module_brightness.append(brightness)

        # 밝기 순으로 정렬 (어두운 것 -> 밝은 것)
        sorted_modules = sorted(modules_info, key=lambda x: x['brightness'])

        return jsonify({
            'success': True,
            'module_count': len(sorted_modules),
            'modules': sorted_modules,
            'brightness_range': {
                'min': float(min(module_brightness)),
                'max': float(max(module_brightness))
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """이미지 생성"""
    try:
        # 파라미터 파싱
        grid_size_str = request.form.get('grid_size', '64x40')
        output_dpi = int(request.form.get('output_dpi', 600))

        try:
            cols, rows = map(int, grid_size_str.split('x'))
            grid_size = (cols, rows)
        except:
            return jsonify({'error': '잘못된 그리드 크기 형식입니다. (예: 64x40)'}), 400

        # 모듈 파일 처리
        module_files = request.files.getlist('module_files')
        if not module_files:
            return jsonify({'error': '모듈 파일을 선택해주세요.'}), 400

        # 임시 폴더 경로 설정
        module_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'modules_gen')
        target_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'targets')
        output_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'outputs')

        # 기존 폴더 삭제 후 재생성 (이전 파일 제거)
        if os.path.exists(module_folder):
            shutil.rmtree(module_folder)
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        # 폴더 생성
        os.makedirs(module_folder, exist_ok=True)
        os.makedirs(target_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        # 모듈 파일 저장
        for file in module_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(module_folder, filename))

        # 타겟 파일 처리
        target_files = request.files.getlist('target_files')
        if not target_files:
            return jsonify({'error': '타겟 파일을 선택해주세요.'}), 400

        # 타겟 파일 저장
        for file in target_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(target_folder, filename))

        # MD 파일 저장 폴더
        md_folder = os.path.join(output_folder, 'md')

        # 이미지 생성 (폴더 일괄 처리)
        process_folder(
            module_folder=module_folder,
            target_folder=target_folder,
            output_folder=output_folder,
            grid_size=grid_size,
            output_dpi=output_dpi,
            invert=False,
            md_folder=md_folder,
            copy_images=True  # 웹에서는 이미지 복사
        )

        # total.md 파일 읽기
        total_md_path = os.path.join(md_folder, 'total.md')
        if not os.path.exists(total_md_path):
            return jsonify({'error': 'total.md 파일이 생성되지 않았습니다.'}), 500

        with open(total_md_path, 'r', encoding='utf-8') as f:
            total_md_content = f.read()

        # 마크다운 내 이미지 경로를 웹 경로로 변경
        # images/modules/xxx.png -> /outputs/md/images/modules/xxx.png
        # images/results/xxx.png -> /outputs/md/images/results/xxx.png
        total_md_content = total_md_content.replace('](images/', '](/outputs/md/images/')

        # 생성된 파일 목록 (파일명 순서대로 정렬)
        import re

        def natural_sort_key(filename):
            """자연스러운 숫자 정렬을 위한 키 함수"""
            parts = re.split(r'(\d+)', filename)
            return [int(part) if part.isdigit() else part.lower() for part in parts]

        output_files = []
        for file in os.listdir(output_folder):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                output_files.append(file)

        # 파일명 자연스러운 순으로 정렬 (1, 2, 3, 10이 아니라 1, 2, 3, 10 순서)
        output_files.sort(key=natural_sort_key)

        return jsonify({
            'success': True,
            'total_md': total_md_content,
            'total_md_path': total_md_path,
            'output_files': output_files,
            'output_count': len(output_files)
        })

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/download-md', methods=['GET'])
def download_md():
    """total.md 파일 다운로드"""
    try:
        md_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'outputs', 'md')
        total_md_path = os.path.join(md_folder, 'total.md')

        if not os.path.exists(total_md_path):
            return jsonify({'error': 'total.md 파일을 찾을 수 없습니다.'}), 404

        return send_file(total_md_path, as_attachment=True, download_name='total.md')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-results', methods=['GET'])
def download_results():
    """결과 파일들을 ZIP으로 다운로드"""
    try:
        import zipfile

        output_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'outputs')

        # ZIP 파일 생성
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'results.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_folder)
                    zipf.write(file_path, arcname)

        return send_file(zip_path, as_attachment=True, download_name='results.zip')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/outputs/<path:filename>')
def output_file(filename):
    """생성된 파일 서빙"""
    output_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'outputs')
    return send_from_directory(output_folder, filename)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """업로드된 파일 서빙"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    import socket

    # 로컬 IP 주소 가져오기
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "IP를 가져올 수 없습니다"

    print("=" * 60)
    print("Module Grid Generator Web App")
    print("=" * 60)
    print()
    print("서버 접속 주소:")
    print(f"  로컬: http://127.0.0.1:5000")
    print(f"  네트워크: http://{local_ip}:5000")
    print()
    print("같은 네트워크(WiFi)에 연결된 다른 기기에서")
    print(f"http://{local_ip}:5000 으로 접속하세요.")
    print()
    print("외부 인터넷에서 접속하려면 포트포워딩이 필요합니다.")
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000)