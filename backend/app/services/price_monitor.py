import re
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from bs4 import BeautifulSoup
from loguru import logger

from app.models.price import PriceHistory, PriceAlert, PriceChangeType
from app.models.alert import Alert, AlertType, AlertSeverity


class PriceMonitor:
    """
    Service for extracting and tracking prices from competitor websites.
    Detects price changes, discounts, and promotions.
    """
    
    # Common currency symbols and codes
    CURRENCY_PATTERNS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        'USD': 'USD',
        'EUR': 'EUR',
        'GBP': 'GBP',
    }
    
    # Price regex patterns (order matters - more specific first)
    PRICE_PATTERNS = [
        # $99.99, €99,99, £99.99 (with decimals)
        r'[\$€£¥₹]\s*(\d{1,3}(?:[,.\s]?\d{3})*(?:[.,]\d{2}))',
        # $99, €99, £99 (simple integers with currency symbol)
        r'[\$€£¥₹]\s*(\d{1,6})',
        # 99.99 USD, 99,99 EUR
        r'(\d{1,3}(?:[,.\s]?\d{3})*(?:[.,]\d{2})?)\s*(?:USD|EUR|GBP|JPY|INR)',
        # /mo, /month, /year pricing (SaaS style)
        r'[\$€£]\s*(\d+(?:[.,]\d{2})?)\s*(?:/mo|/month|/mon|per\s*month)',
        r'[\$€£]\s*(\d+(?:[.,]\d{2})?)\s*(?:/yr|/year|per\s*year|annually)',
        # Starting at $X, From $X patterns
        r'(?:starting|from|starts)\s*(?:at|@)?\s*[\$€£]\s*(\d+(?:[.,]\d{2})?)',
        # Price: $X, Cost: $X patterns  
        r'(?:price|cost|fee)[:=]?\s*[\$€£]\s*(\d+(?:[.,]\d{2})?)',
        # X per user, X per seat patterns
        r'[\$€£]\s*(\d+(?:[.,]\d{2})?)\s*(?:per\s*(?:user|seat|license|month|year))',
    ]
    
    # Discount patterns
    DISCOUNT_PATTERNS = [
        r'(\d+)\s*%\s*off',
        r'save\s*(\d+)\s*%',
        r'(\d+)\s*%\s*discount',
        r'(\d+)\s*%\s*savings',
    ]
    
    def __init__(self):
        self.price_change_threshold = 0.01  # 1% minimum change to trigger alert
        
    def extract_currency(self, text: str) -> str:
        """Extract currency from text."""
        for symbol, code in self.CURRENCY_PATTERNS.items():
            if symbol in text:
                return code
        return 'USD'  # Default
    
    def normalize_price(self, price_str: str) -> Decimal:
        """Normalize price string to Decimal."""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[\$€£¥₹\s]', '', price_str)
        
        # Handle European format (1.234,56) vs US format (1,234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rindex(',') > cleaned.rindex('.'):
                # European format
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Could be thousands separator or decimal
            parts = cleaned.split(',')
            if len(parts[-1]) == 2:
                # Likely decimal
                cleaned = cleaned.replace(',', '.')
            else:
                # Thousands separator
                cleaned = cleaned.replace(',', '')
        
        try:
            return Decimal(cleaned)
        except:
            return Decimal(0)
    
    def extract_prices(self, html: str, url: str) -> List[dict]:
        """Extract all prices from HTML content."""
        soup = BeautifulSoup(html, "lxml")
        prices = []
        
        # Look for common pricing elements (expanded for SaaS/B2B)
        pricing_selectors = [
            '[class*="price"]',
            '[class*="Price"]',
            '[class*="cost"]',
            '[class*="amount"]',
            '[data-price]',
            '[itemprop="price"]',
            # SaaS/B2B pricing patterns
            '[class*="plan"]',
            '[class*="Plan"]',
            '[class*="tier"]',
            '[class*="Tier"]',
            '[class*="pricing"]',
            '[class*="Pricing"]',
            '[class*="subscription"]',
            '[class*="package"]',
            '[class*="fee"]',
            '[class*="rate"]',
        ]
        
        found_elements = set()
        
        for selector in pricing_selectors:
            for element in soup.select(selector):
                text = element.get_text(strip=True)
                
                # Skip if already processed
                if text in found_elements:
                    continue
                found_elements.add(text)
                
                # Try to extract price
                for pattern in self.PRICE_PATTERNS:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        price = self.normalize_price(match)
                        if price > 0:
                            # Try to find product name
                            product_name = self._find_product_name(element, soup)
                            currency = self.extract_currency(text)
                            
                            # Check for original price / discount
                            original_price = None
                            discount_percent = None
                            is_on_sale = False
                            
                            parent = element.parent
                            if parent:
                                parent_text = parent.get_text()
                                
                                # Look for strikethrough / original price
                                strike = parent.find(['s', 'strike', 'del']) or parent.find(class_=re.compile(r'original|was|old', re.I))
                                if strike:
                                    orig_text = strike.get_text()
                                    for p in self.PRICE_PATTERNS:
                                        orig_matches = re.findall(p, orig_text, re.I)
                                        if orig_matches:
                                            original_price = self.normalize_price(orig_matches[0])
                                            if original_price > price:
                                                is_on_sale = True
                                                discount_percent = int((1 - float(price) / float(original_price)) * 100)
                                            break
                                
                                # Look for discount percentage
                                for dp in self.DISCOUNT_PATTERNS:
                                    disc_match = re.search(dp, parent_text, re.I)
                                    if disc_match:
                                        discount_percent = int(disc_match.group(1))
                                        is_on_sale = True
                                        break
                            
                            prices.append({
                                'product_name': product_name or f"Product on {url}",
                                'price': price,
                                'original_price': original_price,
                                'currency': currency,
                                'is_on_sale': is_on_sale,
                                'discount_percent': discount_percent,
                                'source_url': url
                            })
        
        return prices
    
    def _find_product_name(self, price_element, soup) -> Optional[str]:
        """Try to find the product name associated with a price."""
        # Check parent elements for headings or product titles
        current = price_element.parent
        
        for _ in range(5):  # Go up to 5 levels
            if current is None:
                break
            
            # Look for headings
            heading = current.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if heading:
                return heading.get_text(strip=True)[:200]
            
            # Look for product title classes
            title = current.find(class_=re.compile(r'title|name|product', re.I))
            if title:
                text = title.get_text(strip=True)
                if len(text) > 2 and len(text) < 200:
                    return text
            
            current = current.parent
        
        return None
    
    async def process_prices(
        self,
        competitor_id: UUID,
        url: str,
        html: str,
        db
    ) -> dict:
        """Extract prices and track changes."""
        from sqlalchemy import select, and_
        
        extracted = self.extract_prices(html, url)
        
        results = {
            'new': 0,
            'updated': 0,
            'unchanged': 0,
            'alerts': []
        }
        
        for price_data in extracted:
            # Check for existing price record for this product
            result = await db.execute(
                select(PriceHistory)
                .where(and_(
                    PriceHistory.competitor_id == competitor_id,
                    PriceHistory.product_name == price_data['product_name']
                ))
                .order_by(PriceHistory.captured_at.desc())
                .limit(1)
            )
            existing = result.scalar_one_or_none()
            
            # Create new price record
            new_price = PriceHistory(
                competitor_id=competitor_id,
                product_name=price_data['product_name'],
                product_url=price_data['source_url'],
                price=price_data['price'],
                original_price=price_data['original_price'],
                currency=price_data['currency'],
                is_on_sale=price_data['is_on_sale'],
                discount_percent=price_data['discount_percent'],
                captured_at=datetime.utcnow()
            )
            db.add(new_price)
            await db.flush()
            
            if existing:
                old_price = existing.price
                new_price_val = price_data['price']
                
                if old_price != new_price_val:
                    # Price changed
                    change_percent = float((new_price_val - old_price) / old_price * 100)
                    
                    if abs(change_percent) >= self.price_change_threshold * 100:
                        change_type = PriceChangeType.INCREASE if change_percent > 0 else PriceChangeType.DECREASE
                        
                        # Create price alert
                        price_alert = PriceAlert(
                            price_id=new_price.id,
                            change_type=change_type,
                            old_price=old_price,
                            new_price=new_price_val,
                            change_percent=Decimal(str(round(change_percent, 2)))
                        )
                        db.add(price_alert)
                        
                        # Create system alert
                        severity = AlertSeverity.HIGH if abs(change_percent) > 10 else AlertSeverity.MEDIUM
                        
                        alert = Alert(
                            competitor_id=competitor_id,
                            alert_type=AlertType.PRICE_CHANGE,
                            severity=severity,
                            title=f"Price {'Increased' if change_percent > 0 else 'Decreased'}: {price_data['product_name'][:50]}",
                            message=f"Price changed from ${old_price} to ${new_price_val} ({change_percent:+.1f}%)",
                            related_url=price_data['source_url'],
                            related_entity_id=str(new_price.id),
                            related_entity_type="price"
                        )
                        db.add(alert)
                        
                        results['updated'] += 1
                        results['alerts'].append({
                            'product': price_data['product_name'],
                            'old_price': float(old_price),
                            'new_price': float(new_price_val),
                            'change_percent': change_percent
                        })
                    else:
                        results['unchanged'] += 1
                else:
                    results['unchanged'] += 1
            else:
                # New product
                price_alert = PriceAlert(
                    price_id=new_price.id,
                    change_type=PriceChangeType.NEW,
                    old_price=None,
                    new_price=price_data['price'],
                    change_percent=None
                )
                db.add(price_alert)
                results['new'] += 1
        
        await db.commit()
        return results
    
    async def get_price_comparison(
        self,
        product_name: str,
        competitor_ids: List[UUID],
        db
    ) -> dict:
        """Compare prices across competitors."""
        from sqlalchemy import select, and_, func
        
        comparison = {}
        
        for comp_id in competitor_ids:
            # Get latest price for this product from this competitor
            subquery = (
                select(func.max(PriceHistory.captured_at))
                .where(and_(
                    PriceHistory.competitor_id == comp_id,
                    PriceHistory.product_name.ilike(f"%{product_name}%")
                ))
            )
            
            result = await db.execute(
                select(PriceHistory)
                .where(and_(
                    PriceHistory.competitor_id == comp_id,
                    PriceHistory.product_name.ilike(f"%{product_name}%"),
                    PriceHistory.captured_at == subquery.scalar_subquery()
                ))
            )
            
            price_record = result.scalar_one_or_none()
            
            if price_record:
                comparison[str(comp_id)] = {
                    'price': float(price_record.price),
                    'currency': price_record.currency,
                    'is_on_sale': price_record.is_on_sale,
                    'discount_percent': price_record.discount_percent
                }
        
        return comparison
