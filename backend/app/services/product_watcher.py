import re
import json
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from bs4 import BeautifulSoup
from loguru import logger

from app.models.product import Product, ProductFeature
from app.models.alert import Alert, AlertType, AlertSeverity


class ProductWatcher:
    """
    Service for monitoring competitor product catalogs.
    Detects new products, feature changes, and availability updates.
    """
    
    def __init__(self):
        self.feature_patterns = [
            r'✓\s*(.+)',
            r'✔\s*(.+)',
            r'•\s*(.+)',
            r'-\s*(.+)',
        ]
    
    def extract_products(self, html: str, url: str) -> List[dict]:
        """Extract product information from HTML."""
        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # Common product container selectors
        product_selectors = [
            '[class*="product"]',
            '[class*="Product"]',
            '[itemtype*="Product"]',
            '[data-product]',
            'article[class*="card"]',
        ]
        
        seen_names = set()
        
        for selector in product_selectors:
            for element in soup.select(selector):
                product = self._extract_product_data(element, url)
                
                if product and product['name'] and product['name'] not in seen_names:
                    seen_names.add(product['name'])
                    products.append(product)
        
        return products
    
    def _extract_product_data(self, element, base_url: str) -> Optional[dict]:
        """Extract product data from an element."""
        # Find product name
        name = None
        name_elem = element.find(['h1', 'h2', 'h3', 'h4']) or element.find(class_=re.compile(r'name|title', re.I))
        if name_elem:
            name = name_elem.get_text(strip=True)
        
        if not name or len(name) < 2:
            return None
        
        # Find product URL
        url = None
        link = element.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('/'):
                from urllib.parse import urljoin
                url = urljoin(base_url, href)
            elif href.startswith('http'):
                url = href
        
        # Find product image
        image_url = None
        img = element.find('img')
        if img:
            image_url = img.get('src') or img.get('data-src')
        
        # Find description
        description = None
        desc_elem = element.find(class_=re.compile(r'desc|summary|excerpt', re.I))
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:1000]
        
        # Find category
        category = None
        cat_elem = element.find(class_=re.compile(r'category|cat|type', re.I))
        if cat_elem:
            category = cat_elem.get_text(strip=True)
        
        # Check availability
        is_available = True
        unavail_elem = element.find(text=re.compile(r'out of stock|unavailable|sold out', re.I))
        if unavail_elem:
            is_available = False
        
        # Extract features
        features = self._extract_features(element)
        
        return {
            'name': name[:500],
            'url': url or base_url,
            'description': description,
            'short_description': description[:200] if description else None,
            'category': category,
            'image_url': image_url,
            'is_available': is_available,
            'features': features
        }
    
    def _extract_features(self, element) -> List[dict]:
        """Extract product features from an element."""
        features = []
        
        # Look for feature lists
        feature_lists = element.find_all(['ul', 'ol'], class_=re.compile(r'feature|spec|benefit', re.I))
        
        for feature_list in feature_lists:
            for item in feature_list.find_all('li'):
                text = item.get_text(strip=True)
                if text and len(text) > 2:
                    features.append({
                        'name': text[:250],
                        'value': None,
                        'category': 'general'
                    })
        
        # Look for spec tables
        spec_tables = element.find_all('table', class_=re.compile(r'spec|feature|detail', re.I))
        
        for table in spec_tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    features.append({
                        'name': cells[0].get_text(strip=True)[:250],
                        'value': cells[1].get_text(strip=True)[:500],
                        'category': 'specification'
                    })
        
        return features[:50]  # Limit features
    
    async def process_products(
        self,
        competitor_id: UUID,
        url: str,
        html: str,
        db
    ) -> dict:
        """Process extracted products and track changes."""
        from sqlalchemy import select
        import hashlib
        
        extracted = self.extract_products(html, url)
        
        results = {
            'new': 0,
            'updated': 0,
            'unchanged': 0,
            'unavailable': 0
        }
        
        for product_data in extracted:
            # Check for existing product
            result = await db.execute(
                select(Product).where(
                    Product.competitor_id == competitor_id,
                    Product.name == product_data['name']
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Check for changes
                desc_hash = hashlib.sha256(
                    (product_data['description'] or '').encode()
                ).hexdigest()
                
                changed = False
                
                if existing.description_hash != desc_hash:
                    existing.description = product_data['description']
                    existing.short_description = product_data['short_description']
                    existing.description_hash = desc_hash
                    changed = True
                
                if existing.is_available != product_data['is_available']:
                    existing.is_available = product_data['is_available']
                    changed = True
                    
                    if not product_data['is_available']:
                        results['unavailable'] += 1
                        
                        # Create alert for availability change
                        alert = Alert(
                            competitor_id=competitor_id,
                            alert_type=AlertType.AVAILABILITY_CHANGE,
                            severity=AlertSeverity.MEDIUM,
                            title=f"Product Unavailable: {product_data['name'][:50]}",
                            message=f"Product is now out of stock",
                            related_url=product_data['url'],
                            related_entity_id=str(existing.id),
                            related_entity_type="product"
                        )
                        db.add(alert)
                
                existing.image_url = product_data['image_url']
                existing.category = product_data['category']
                existing.last_checked = datetime.utcnow()
                existing.is_new = False
                
                if changed:
                    results['updated'] += 1
                else:
                    results['unchanged'] += 1
            else:
                # New product
                desc_hash = hashlib.sha256(
                    (product_data['description'] or '').encode()
                ).hexdigest()
                
                product = Product(
                    competitor_id=competitor_id,
                    name=product_data['name'],
                    url=product_data['url'],
                    description=product_data['description'],
                    short_description=product_data['short_description'],
                    category=product_data['category'],
                    image_url=product_data['image_url'],
                    is_available=product_data['is_available'],
                    is_new=True,
                    first_seen=datetime.utcnow(),
                    last_checked=datetime.utcnow(),
                    description_hash=desc_hash
                )
                db.add(product)
                await db.flush()
                
                # Add features
                for feature in product_data['features']:
                    pf = ProductFeature(
                        product_id=product.id,
                        feature_name=feature['name'],
                        feature_value=feature['value'],
                        feature_category=feature['category']
                    )
                    db.add(pf)
                
                # Create alert
                alert = Alert(
                    competitor_id=competitor_id,
                    alert_type=AlertType.NEW_PRODUCT,
                    severity=AlertSeverity.HIGH,
                    title=f"New Product: {product_data['name'][:50]}",
                    message=f"Competitor launched a new product",
                    related_url=product_data['url'],
                    related_entity_id=str(product.id),
                    related_entity_type="product"
                )
                db.add(alert)
                
                results['new'] += 1
        
        await db.commit()
        return results
    
    async def compare_features(
        self,
        product_names: List[str],
        competitor_ids: List[UUID],
        db
    ) -> List[dict]:
        """Compare features across similar products."""
        from sqlalchemy import select
        
        feature_matrix = {}
        
        for comp_id in competitor_ids:
            for name in product_names:
                # Find matching product
                result = await db.execute(
                    select(Product).where(
                        Product.competitor_id == comp_id,
                        Product.name.ilike(f"%{name}%")
                    ).limit(1)
                )
                product = result.scalar_one_or_none()
                
                if product:
                    # Get features
                    features_result = await db.execute(
                        select(ProductFeature).where(
                            ProductFeature.product_id == product.id
                        )
                    )
                    
                    for feature in features_result.scalars().all():
                        if feature.feature_name not in feature_matrix:
                            feature_matrix[feature.feature_name] = {}
                        
                        feature_matrix[feature.feature_name][str(comp_id)] = feature.feature_value or "✓"
        
        return [
            {'feature_name': name, 'values': values}
            for name, values in feature_matrix.items()
        ]
