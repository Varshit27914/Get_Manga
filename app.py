from flask import Flask, request, send_file, send_from_directory, jsonify
import cloudscraper
from bs4 import BeautifulSoup
from fpdf import FPDF
import os
import tempfile

app = Flask(__name__, static_folder='static')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data['url']
    scraper = cloudscraper.create_scraper()

    try:
        res = scraper.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')

        domain = url.split("/")[2]
        img_tags = []

        if "mangakakalot" in domain:
            container = soup.find('div', class_='container-chapter-reader')
            if container:
                img_tags = container.find_all('img')

        elif "mangabuddy" in domain:
            container = soup.find('div', class_='reading-content')
            if container:
                img_tags = container.find_all('img')

        img_urls = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                img_urls.append(src)

        if not img_urls:
            return jsonify({'error': 'No images found'}), 404

        # Generate PDF
        pdf = FPDF()
        for img_url in img_urls:
            try:
                img_data = scraper.get(img_url).content
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(img_data)
                    pdf.add_page()
                    pdf.image(f.name, x=10, y=10, w=190)
                    os.unlink(f.name)
            except:
                continue  # Skip any failed images

        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(pdf_file.name)

        return send_file(pdf_file.name, as_attachment=True, download_name='manga.pdf')

    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
