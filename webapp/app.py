from flask import Flask, render_template, request, jsonify
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

@app.route('/')
def index():
    """Main page with map and input form."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process the analysis request."""
    try:
        data = request.get_json()
        
        # Extract polygon coordinates
        polygon = data.get('polygon')
        
        # Extract analysis parameters
        params = {
            'historical_start': data.get('historical_start', '1990-01-01'),
            'historical_end': data.get('historical_end', '2000-01-01'),
            'recent_start': data.get('recent_start', '2015-01-01'),
            'recent_end': data.get('recent_end', '2025-01-01'),
            'month': int(data.get('month', 6)),
            'cloud_cover': int(data.get('cloud_cover', 10)),
            'output_name': data.get('output_name', 'snow_analysis'),
            'clip_to_region': data.get('clip_to_region', False)
        }
        
        # Log received data
        print(f"Received polygon with {len(polygon)} coordinates")
        print(f"Analysis parameters: {params}")
        
        # Return success - actual analysis integration would go here
        return jsonify({
            'status': 'success',
            'message': 'Analysis parameters received',
            'polygon_points': len(polygon),
            'params': params
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
