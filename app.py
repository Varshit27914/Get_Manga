from flask import Flask, request, send_file, send_from_directory, jsonify
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os
import tempfile

app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data['url']
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'html.parser')

        domain = url.split("/")[2]
        img_tags = []

        if "mangakakalot" in domain:
            # Mangakakalot-specific container
            container = soup.find('div', class_='container-chapter-reader')
            if container:
                img_tags = container.find_all('img')

        elif "mangabuddy" in domain:
            # Mangabuddy-specific container
            container = soup.find('div', class_='reading-content')
            if container:
                img_tags = container.find_all('img')

        # Collect image URLs
        img_urls = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and ('.jpg' in src or '.png' in src):
                img_urls.append(src)

        if not img_urls:
            return jsonify({'error': 'No images found'}), 404

        # Generate PDF
        pdf = FPDF()
        for img_url in img_urls:
            img_data = requests.get(img_url, headers=headers).content
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                f.write(img_data)
                pdf.add_page()
                pdf.image(f.name, x=10, y=10, w=190)
                os.unlink(f.name)

        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(pdf_file.name)

        return send_file(pdf_file.name, as_attachment=True, download_name='manga.pdf')

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
