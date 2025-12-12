"""
Price Service - Servicio para obtener precios de criptomonedas desde CoinGecko
Proporciona precios en USD y EUR con cache para evitar exceder rate limits.
"""

import logging
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PriceService:
    """Servicio para obtener precios de criptomonedas usando CoinGecko API."""
    
    COINGECKO_API = 'https://api.coingecko.com/api/v3'
    
    CRYPTO_IDS = {
        'TON': 'the-open-network',
        'USDT': 'tether',
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'B3C': None,
    }
    
    B3C_FIXED_PRICE_USD = 0.10
    
    CACHE_DURATION_SECONDS = 120
    
    def __init__(self):
        """Inicializar el servicio de precios."""
        self._price_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._eur_rate_cache: Optional[float] = None
        self._eur_rate_timestamp: Optional[datetime] = None
        logger.info("PriceService initialized")
    
    def _is_cache_valid(self) -> bool:
        """Verificar si el cache de precios sigue válido."""
        if self._cache_timestamp is None:
            return False
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self.CACHE_DURATION_SECONDS
    
    def _is_eur_rate_valid(self) -> bool:
        """Verificar si el cache del tipo de cambio EUR sigue válido."""
        if self._eur_rate_timestamp is None:
            return False
        elapsed = (datetime.now() - self._eur_rate_timestamp).total_seconds()
        return elapsed < self.CACHE_DURATION_SECONDS * 5
    
    def _fetch_prices(self) -> Dict[str, Dict[str, float]]:
        """Obtener precios de CoinGecko API."""
        try:
            coin_ids = [cid for cid in self.CRYPTO_IDS.values() if cid is not None]
            ids_param = ','.join(coin_ids)
            
            url = f"{self.COINGECKO_API}/simple/price"
            params = {
                'ids': ids_param,
                'vs_currencies': 'usd,eur'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for symbol, coin_id in self.CRYPTO_IDS.items():
                    if coin_id and coin_id in data:
                        prices[symbol] = {
                            'usd': data[coin_id].get('usd', 0),
                            'eur': data[coin_id].get('eur', 0)
                        }
                
                eur_rate = self._calculate_eur_rate(prices)
                if eur_rate:
                    prices['B3C'] = {
                        'usd': self.B3C_FIXED_PRICE_USD,
                        'eur': self.B3C_FIXED_PRICE_USD * eur_rate
                    }
                else:
                    prices['B3C'] = {
                        'usd': self.B3C_FIXED_PRICE_USD,
                        'eur': self.B3C_FIXED_PRICE_USD * 0.92
                    }
                
                self._price_cache = prices
                self._cache_timestamp = datetime.now()
                
                logger.info(f"Prices updated: {prices}")
                return prices
            else:
                logger.warning(f"CoinGecko API returned status {response.status_code}")
                return self._get_fallback_prices()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching prices from CoinGecko: {e}")
            return self._get_fallback_prices()
        except Exception as e:
            logger.error(f"Unexpected error fetching prices: {e}")
            return self._get_fallback_prices()
    
    def _calculate_eur_rate(self, prices: Dict) -> Optional[float]:
        """Calcular tasa EUR/USD basándose en los precios de USDT."""
        try:
            if 'USDT' in prices:
                usdt_usd = prices['USDT'].get('usd', 1)
                usdt_eur = prices['USDT'].get('eur', 0.92)
                if usdt_usd > 0:
                    rate = usdt_eur / usdt_usd
                    self._eur_rate_cache = rate
                    self._eur_rate_timestamp = datetime.now()
                    return rate
        except Exception:
            pass
        return self._eur_rate_cache or 0.92
    
    def _get_fallback_prices(self) -> Dict[str, Dict[str, float]]:
        """Obtener precios de respaldo en caso de error."""
        if self._price_cache:
            return self._price_cache
        
        return {
            'TON': {'usd': 5.5, 'eur': 5.06},
            'USDT': {'usd': 1.0, 'eur': 0.92},
            'BTC': {'usd': 42000, 'eur': 38640},
            'ETH': {'usd': 2200, 'eur': 2024},
            'B3C': {'usd': self.B3C_FIXED_PRICE_USD, 'eur': self.B3C_FIXED_PRICE_USD * 0.92}
        }
    
    def get_prices(self, force_refresh: bool = False) -> Dict[str, Dict[str, float]]:
        """
        Obtener precios actuales de todas las criptomonedas soportadas.
        
        Args:
            force_refresh: Forzar actualización ignorando cache
            
        Returns:
            Dict con precios en USD y EUR por símbolo
        """
        if not force_refresh and self._is_cache_valid():
            return self._price_cache
        
        return self._fetch_prices()
    
    def get_price(self, symbol: str, currency: str = 'usd') -> float:
        """
        Obtener precio de una criptomoneda específica.
        
        Args:
            symbol: Símbolo del token (TON, USDT, B3C, etc.)
            currency: Moneda de destino (usd o eur)
            
        Returns:
            Precio en la moneda especificada
        """
        prices = self.get_prices()
        symbol_upper = symbol.upper()
        currency_lower = currency.lower()
        
        if symbol_upper in prices:
            return prices[symbol_upper].get(currency_lower, 0)
        
        return 0
    
    def calculate_total_balance(self, token_balances: list, currency: str = 'usd') -> Dict[str, Any]:
        """
        Calcular el balance total de todos los tokens en USD o EUR.
        
        Args:
            token_balances: Lista de dicts con 'symbol' y 'balance'
            currency: Moneda de destino (usd o eur)
            
        Returns:
            Dict con total y desglose por token
        """
        prices = self.get_prices()
        currency_lower = currency.lower()
        
        total = 0.0
        breakdown = []
        
        for token in token_balances:
            symbol = token.get('symbol', '').upper()
            balance = float(token.get('balance', 0))
            
            if balance <= 0:
                continue
            
            price = 0
            if symbol in prices:
                price = prices[symbol].get(currency_lower, 0)
            
            value = balance * price
            total += value
            
            breakdown.append({
                'symbol': symbol,
                'balance': balance,
                'price': price,
                'value': value
            })
        
        return {
            'total': round(total, 2),
            'currency': currency_lower.upper(),
            'breakdown': breakdown,
            'prices': prices,
            'last_update': self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }
    
    def get_eur_usd_rate(self) -> float:
        """Obtener tasa de cambio EUR/USD."""
        if self._is_eur_rate_valid() and self._eur_rate_cache:
            return self._eur_rate_cache
        
        self.get_prices()
        return self._eur_rate_cache or 0.92


price_service = PriceService()
