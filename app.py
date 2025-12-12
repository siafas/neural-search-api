#!/usr/bin/env python3
"""
Neural Search API for OpenCart Chatbot
Multi-tenant support - One server serves multiple shops
"""

from flask import Flask, request, jsonify
import os
import json
import time
import re
import threading
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
MODELS_DIR = Path("/tmp/models")
MODELS_DIR.mkdir(exist_ok=True)

# Global storage for models (loaded on demand)
loaded_models = {}

# Global variable to track training status
training_status = {}

# =============================================================================
# Neural Search Engine
# =============================================================================

class NeuralSearchEngine:
    """Neural search with fuzzy fallback and configurable boosting"""
    
    def __init__(self, shop_id: str):
        self.shop_id = shop_id
        self.model_path = MODELS_DIR / f"shop_{shop_id}.json"
        self.embedder = None
        self.products = []
        self.embeddings = None
        
    def load_model(self):
        """Load sentence transformer model (lazy loading)"""
        if self.embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence-transformers model...")
                self.embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
    
    def strip_html(self, text: str) -> str:
        """Remove HTML tags and clean whitespace"""
        if not text:
            return ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_text(self, element, tag: str) -> str:
        """Safely extract and clean text from XML element"""
        node = element.find(tag)
        if node is not None and node.text:
            return self.strip_html(node.text)
        return ''
    
    def train(self, xml_content: str) -> Dict:
        """Train model from XML content"""
        import xml.etree.ElementTree as ET
        from rapidfuzz import fuzz
        import numpy as np
        
        self.load_model()
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            products = []
            
            for product in root.findall('.//product'):
                product_data = {
                    'id': self.get_text(product, 'id'),
                    'name': self.get_text(product, 'name'),
                    'model': self.get_text(product, 'mpn') or self.get_text(product, 'model'),
                    'description': self.get_text(product, 'description'),
                    'category': self.get_text(product, 'category'),
                    'season': self.get_text(product, 'season'),
                    'gender': self.get_text(product, 'gender'),
                    'kind_of': self.get_text(product, 'kind_of'),
                    'fit': self.get_text(product, 'fit'),
                    'color': self.get_text(product, 'color'),
                    'manufacturer': self.get_text(product, 'manufacturer'),
                    'price': self.get_text(product, 'price_with_vat') or self.get_text(product, 'price'),
                    'image': self.get_text(product, 'image'),
                    'url': self.get_text(product, 'link') or self.get_text(product, 'url'),
                }
                
                # Build rich search text with ALL fields for better semantic matching
                search_text_parts = [
                    product_data['name'],
                    product_data['model'],
                    product_data['description'][:500],  # Limit description length
                    product_data['category'],
                    product_data['season'],
                    product_data['gender'],
                    product_data['kind_of'],
                    product_data['fit'],
                    product_data['color'],
                    product_data['manufacturer']
                ]
                
                # Filter out empty strings and join
                search_text = ' '.join(filter(None, search_text_parts))
                product_data['search_text'] = search_text
                
                products.append(product_data)
            
            if not products:
                return {'success': False, 'error': 'No products found in XML'}
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(products)} products...")
            search_texts = [p['search_text'] for p in products]
            embeddings = self.embedder.encode(search_texts, convert_to_numpy=True)
            
            # Save model
            model_data = {
                'shop_id': self.shop_id,
                'products': products,
                'embeddings': embeddings.tolist(),
                'trained_at': time.time()
            }
            
            with open(self.model_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2)
            
            self.products = products
            self.embeddings = embeddings
            
            logger.info(f"Training complete for shop {self.shop_id}: {len(products)} products")
            
            return {
                'success': True,
                'shop_id': self.shop_id,
                'products_count': len(products),
                'trained_at': model_data['trained_at']
            }
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return {'success': False, 'error': str(e)}
    
    def load(self) -> bool:
        """Load trained model from disk"""
        if not self.model_path.exists():
            return False
        
        try:
            import numpy as np
            
            with open(self.model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            self.products = model_data['products']
            self.embeddings = np.array(model_data['embeddings'])
            
            logger.info(f"Loaded model for shop {self.shop_id}: {len(self.products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def search(self, query: str, limit: int = 5, boost_config: Dict = None, min_threshold: float = 0.0) -> List[Dict]:
        """
        Search products using neural + fuzzy approach with configurable boosting
        
        Args:
            query: Search query
            limit: Max results to return
            boost_config: Dict with boost weights e.g. {'season': 0.15, 'category': 0.10}
            min_threshold: Minimum score threshold (0.0 - 1.0)
        """
        from rapidfuzz import fuzz
        import numpy as np
        
        if not self.products:
            if not self.load():
                return []
        
        self.load_model()
        
        # Default boost config
        if boost_config is None:
            boost_config = {}
        
        try:
            # Neural search
            query_embedding = self.embedder.encode([query], convert_to_numpy=True)[0]
            similarities = np.dot(self.embeddings, query_embedding)
            
            # Fuzzy search scores
            fuzzy_scores = []
            for product in self.products:
                score = max(
                    fuzz.partial_ratio(query.lower(), (product.get('name') or '').lower()),
                    fuzz.partial_ratio(query.lower(), (product.get('model') or '').lower()),
                    fuzz.partial_ratio(query.lower(), (product.get('description') or '').lower()),
                    fuzz.partial_ratio(query.lower(), (product.get('category') or '').lower()),
                    fuzz.partial_ratio(query.lower(), (product.get('season') or '').lower()),
                    fuzz.partial_ratio(query.lower(), (product.get('gender') or '').lower())
                ) / 100.0
                fuzzy_scores.append(score)
            
            # Combine scores (70% neural, 30% fuzzy)
            combined_scores = 0.7 * similarities + 0.3 * np.array(fuzzy_scores)
            
            # APPLY BOOSTING based on attribute matches
            query_lower = query.lower()
            boosted_scores = combined_scores.copy()
            
            for idx, product in enumerate(self.products):
                boost = 0.0
                
                # Season boost
                if boost_config.get('season', 0) > 0:
                    season = (product.get('season') or '').lower()
                    if season:
                        # Check for seasonal keywords in query
                        if ('καλοκαίρι' in query_lower or 'summer' in query_lower) and 'καλοκαιρ' in season:
                            boost += boost_config['season']
                        elif ('χειμώνα' in query_lower or 'κρύο' in query_lower or 'winter' in query_lower) and 'χειμ' in season:
                            boost += boost_config['season']
                        elif ('άνοιξη' in query_lower or 'spring' in query_lower) and 'ανοιξ' in season:
                            boost += boost_config['season']
                        elif ('φθινόπωρο' in query_lower or 'autumn' in query_lower or 'fall' in query_lower) and 'φθιν' in season:
                            boost += boost_config['season']
                
                # Category boost
                if boost_config.get('category', 0) > 0:
                    category = (product.get('category') or '').lower()
                    if category and category in query_lower:
                        boost += boost_config['category']
                
                # Manufacturer boost
                if boost_config.get('manufacturer', 0) > 0:
                    manufacturer = (product.get('manufacturer') or '').lower()
                    if manufacturer and manufacturer in query_lower:
                        boost += boost_config['manufacturer']
                
                # Color boost
                if boost_config.get('color', 0) > 0:
                    color = (product.get('color') or '').lower()
                    if color and color in query_lower:
                        boost += boost_config['color']
                
                # Gender boost
                if boost_config.get('gender', 0) > 0:
                    gender = (product.get('gender') or '').lower()
                    if gender and gender in query_lower:
                        boost += boost_config['gender']
                
                # Fit boost
                if boost_config.get('fit', 0) > 0:
                    fit = (product.get('fit') or '').lower()
                    if fit and any(word in query_lower for word in fit.split()):
                        boost += boost_config['fit']
                
                # Kind_of boost
                if boost_config.get('kind_of', 0) > 0:
                    kind_of = (product.get('kind_of') or '').lower()
                    if kind_of and kind_of in query_lower:
                        boost += boost_config['kind_of']
                
                boosted_scores[idx] += boost
            
            # Sort by boosted scores
            sorted_indices = np.argsort(boosted_scores)[::-1]
            
            # APPLY THRESHOLD FILTER
            if min_threshold > 0:
                filtered_indices = [i for i in sorted_indices if boosted_scores[i] >= min_threshold]
            else:
                filtered_indices = sorted_indices
            
            # Get top results up to limit
            top_indices = filtered_indices[:limit]
            
            results = []
            for idx in top_indices:
                product = self.products[idx].copy()
                product['score'] = float(boosted_scores[idx])
                product['base_score'] = float(combined_scores[idx])
                product['neural_score'] = float(similarities[idx])
                product['fuzzy_score'] = float(fuzzy_scores[idx])
                results.append(product)
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

# =============================================================================
# Background Training
# =============================================================================

def background_train(shop_id: str, xml_content: str):
    """Background training task"""
    try:
        logger.info(f"Background training started for shop {shop_id}")
        
        engine = NeuralSearchEngine(shop_id)
        result = engine.train(xml_content)
        
        if result['success']:
            # Cache the trained model
            loaded_models[shop_id] = engine
            
            training_status[shop_id] = {
                'status': 'completed',
                'completed_at': time.time(),
                'products_count': result['products_count'],
                'message': 'Training completed successfully'
            }
            logger.info(f"Background training completed for shop {shop_id}")
        else:
            training_status[shop_id] = {
                'status': 'failed',
                'completed_at': time.time(),
                'error': result.get('error', 'Unknown error'),
                'message': 'Training failed'
            }
            logger.error(f"Background training failed for shop {shop_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Background training error for shop {shop_id}: {e}")
        training_status[shop_id] = {
            'status': 'failed',
            'completed_at': time.time(),
            'error': str(e),
            'message': 'Training failed'
        }

# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'neural-search-api',
        'version': '2.1.0'
    })

@app.route('/search', methods=['GET'])
def search():
    """
    Search products for a shop with configurable boosting
    
    Query params:
        shop_id (required): Shop identifier
        q (required): Search query
        limit (optional): Max results (default: 5)
        min_threshold (optional): Minimum score threshold (default: 0.0)
        boost_season (optional): Season boost weight (default: 0.0)
        boost_category (optional): Category boost weight (default: 0.0)
        boost_manufacturer (optional): Manufacturer boost weight (default: 0.0)
        boost_color (optional): Color boost weight (default: 0.0)
        boost_gender (optional): Gender boost weight (default: 0.0)
        boost_fit (optional): Fit boost weight (default: 0.0)
        boost_kind_of (optional): Kind_of boost weight (default: 0.0)
    """
    shop_id = request.args.get('shop_id')
    query = request.args.get('q')
    limit = int(request.args.get('limit', 5))
    
    # Get boost configuration from query params
    boost_config = {
        'season': float(request.args.get('boost_season', 0.0)),
        'category': float(request.args.get('boost_category', 0.0)),
        'manufacturer': float(request.args.get('boost_manufacturer', 0.0)),
        'color': float(request.args.get('boost_color', 0.0)),
        'gender': float(request.args.get('boost_gender', 0.0)),
        'fit': float(request.args.get('boost_fit', 0.0)),
        'kind_of': float(request.args.get('boost_kind_of', 0.0)),
    }
    
    min_threshold = float(request.args.get('min_threshold', 0.0))
    
    if not shop_id:
        return jsonify({'error': 'shop_id is required'}), 400
    
    if not query:
        return jsonify({'error': 'q (query) is required'}), 400
    
    # Validate shop_id (alphanumeric only for security)
    if not shop_id.isalnum():
        return jsonify({'error': 'Invalid shop_id'}), 400
    
    try:
        # Get or create engine for this shop
        if shop_id not in loaded_models:
            engine = NeuralSearchEngine(shop_id)
            if not engine.load():
                return jsonify({
                    'error': 'Model not trained for this shop',
                    'shop_id': shop_id
                }), 404
            loaded_models[shop_id] = engine
        else:
            engine = loaded_models[shop_id]
        
        # Search with boosting
        results = engine.search(query, limit, boost_config, min_threshold)
        
        return jsonify({
            'success': True,
            'shop_id': shop_id,
            'query': query,
            'results': results,
            'count': len(results),
            'boost_config': boost_config,
            'min_threshold': min_threshold
        })
        
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/train', methods=['POST'])
def train():
    """
    Train model for a shop (async)
    Returns immediately, training happens in background
    
    POST body (JSON):
        {
            "shop_id": "shop1",
            "xml": "<products>...</products>"
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    
    shop_id = data.get('shop_id')
    xml_content = data.get('xml')
    
    if not shop_id:
        return jsonify({'error': 'shop_id is required'}), 400
    
    if not xml_content:
        return jsonify({'error': 'xml content is required'}), 400
    
    # Validate shop_id
    if not shop_id.isalnum():
        return jsonify({'error': 'Invalid shop_id'}), 400
    
    # Set status to "training"
    training_status[shop_id] = {
        'status': 'training',
        'started_at': time.time(),
        'message': 'Training in progress...'
    }
    
    # Start training in background thread
    thread = threading.Thread(
        target=background_train,
        args=(shop_id, xml_content)
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"Training started in background for shop {shop_id}")
    
    return jsonify({
        'success': True,
        'message': 'Training started in background',
        'shop_id': shop_id,
        'status': 'training'
    })

@app.route('/training-status', methods=['GET'])
def get_training_status():
    """
    Get training status for a shop
    
    Query params:
        shop_id (required): Shop identifier
    """
    shop_id = request.args.get('shop_id')
    
    if not shop_id:
        return jsonify({'error': 'shop_id is required'}), 400
    
    if not shop_id.isalnum():
        return jsonify({'error': 'Invalid shop_id'}), 400
    
    status = training_status.get(shop_id, {
        'status': 'unknown',
        'message': 'No training records found'
    })
    
    return jsonify({
        'shop_id': shop_id,
        **status
    })

@app.route('/status', methods=['GET'])
def status():
    """
    Get model status for a shop
    
    Query params:
        shop_id (required): Shop identifier
    """
    shop_id = request.args.get('shop_id')
    
    if not shop_id:
        return jsonify({'error': 'shop_id is required'}), 400
    
    if not shop_id.isalnum():
        return jsonify({'error': 'Invalid shop_id'}), 400
    
    model_path = MODELS_DIR / f"shop_{shop_id}.json"
    
    if not model_path.exists():
        return jsonify({
            'trained': False,
            'shop_id': shop_id
        })
    
    try:
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        return jsonify({
            'trained': True,
            'shop_id': shop_id,
            'products_count': len(model_data['products']),
            'trained_at': model_data['trained_at']
        })
        
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/shops', methods=['GET'])
def list_shops():
    """List all trained shops"""
    shops = []
    
    for model_file in MODELS_DIR.glob("shop_*.json"):
        try:
            shop_id = model_file.stem.replace('shop_', '')
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            
            shops.append({
                'shop_id': shop_id,
                'products_count': len(model_data['products']),
                'trained_at': model_data['trained_at']
            })
        except:
            continue
    
    return jsonify({
        'shops': shops,
        'count': len(shops)
    })

# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
